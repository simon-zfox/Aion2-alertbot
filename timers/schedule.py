import asyncio
import logging
from copy import copy
from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import aiohttp

from timers.config import REGIONS
from timers.json_file import DATA_DIRECTORY, read_json, write_json


SOURCE_URL = "https://shugo.gg/timers.json"
logger = logging.getLogger(__name__)
WEEKDAYS = {day: index for index, day in enumerate(("mon", "tue", "wed", "thu", "fri", "sat", "sun"))}


def minutes(value: int) -> timedelta:
    if type(value) is not int or not 0 <= value <= 1440:
        raise ValueError("Ungültige Dauer in Minuten.")
    return timedelta(minutes=value)


def clock_time(value: str) -> time:
    parsed = time.fromisoformat(value)
    if parsed.tzinfo is not None or len(value) != 5:
        raise ValueError("Uhrzeiten müssen HH:MM entsprechen.")
    return parsed


@dataclass(frozen=True)
class Event:
    event_id: str
    name: str
    emoji: str
    kind: str
    zone: ZoneInfo
    times: tuple[time, ...]
    days: frozenset[int]
    duration: timedelta
    windows: tuple[tuple[time, time], ...]
    portal: timedelta | None

    @classmethod
    def parse(cls, event: dict, region: str, zone: ZoneInfo) -> "Event":
        for field in ("id", "name", "icon", "kind"):
            if not isinstance(event[field], str) or not event[field].strip():
                raise ValueError(f"Ungültiges Event-Feld: {field}")
        if len(event["name"]) + len(event["icon"]) + 1 > 256:
            raise ValueError("Event-Name überschreitet das Discord-Limit.")
        schedule = event["schedules"][region]
        zone = ZoneInfo(schedule["timeZone"]) if "timeZone" in schedule else zone
        kind = schedule["type"]
        times, windows = (), ()
        days = frozenset(range(7))
        duration = minutes(event["durationMinutes"]) if kind != "windows" else timedelta()
        if kind == "hourly":
            minute = schedule["minute"]
            if type(minute) is not int:
                raise ValueError("Ungültige Minute.")
            times = tuple(time(hour, minute) for hour in range(24))
        elif kind in {"daily", "weekly"}:
            times = tuple(clock_time(value) for value in schedule["times"])
            if kind == "weekly":
                days = frozenset(WEEKDAYS[day] for day in schedule["days"])
        elif kind == "windows":
            windows = tuple((clock_time(w["start"]), clock_time(w["end"])) for w in schedule["windows"])
        else:
            raise ValueError(f"Unbekannter Zeitplantyp: {kind}")
        if not days or not (times or windows):
            raise ValueError("Zeitplan enthält keine Termine.")
        portal = minutes(event["portalMinutes"]) if "portalMinutes" in event else None
        if portal is not None and portal > duration:
            raise ValueError("Portalphase ist länger als das Event.")
        return cls(event["id"], event["name"], event["icon"], event["kind"], zone,
                   times, days, duration, windows, portal)

    def slots(self, day: date):
        if day.weekday() not in self.days:
            return
        for value in self.times:
            start = datetime.combine(day, value, self.zone).astimezone(UTC)
            yield start, start + self.duration
        for begin, finish in self.windows:
            start = datetime.combine(day, begin, self.zone)
            end = datetime.combine(day, finish, self.zone)
            if finish <= begin:
                end += timedelta(days=1)
            yield start.astimezone(UTC), end.astimezone(UTC)


@dataclass(frozen=True)
class Occurrence:
    event_id: str
    name: str
    emoji: str
    starts_at: datetime
    ends_at: datetime
    active: bool
    kind: str
    portal_ends_at: datetime | None = None


class Schedule:
    def __init__(self, data_directory: Path = DATA_DIRECTORY) -> None:
        self.cache_path = data_directory / "shugo-timers.json"
        self.region_id = "global-as"
        self.events: tuple[Event, ...] = ()
        self.available = False
        self._payload = None
        try:
            payload = read_json(self.cache_path)
            self._apply(payload, self._prepare(payload))
        except (OSError, ValueError, KeyError, TypeError) as error:
            logger.warning("Keine gültige Shugo-Kopie vorhanden: %s", error)

    def _prepare(self, payload: dict) -> dict[str, tuple[ZoneInfo, tuple[Event, ...]]]:
        date.fromisoformat(payload["updatedAt"])
        regions = {region["id"]: region for region in payload["regions"]}
        required = {self.region_id, *(region_id for _, region_id in REGIONS.values())}
        if not required.issubset(regions):
            raise ValueError("Eine unterstützte Zeitplanregion fehlt.")
        ids = [event["id"] for event in payload["events"]]
        if len(set(ids)) != len(ids):
            raise ValueError("Doppelte Shugo-Event-IDs.")
        return {region_id: self._prepare_region(payload, region_id, ZoneInfo(region["timeZone"]))
                for region_id, region in regions.items()}

    def _prepare_region(
        self, payload: dict, region_id: str, zone: ZoneInfo,
    ) -> tuple[ZoneInfo, tuple[Event, ...]]:
        selected = [event for event in payload["events"] if region_id in event["schedules"]]
        if not selected:
            raise ValueError("Shugo liefert keine Events für die konfigurierte Region.")
        events = tuple(Event.parse(event, region_id, zone) for event in selected)
        counts = [sum(event.kind == kind for event in events) for kind in ("boss", "reset")]
        counts.append(len(events) - sum(counts))
        if max(counts) > 25 or sum(len(e.name) + len(e.emoji) + 180 for e in events) > 5400:
            raise ValueError("Zeitplandaten überschreiten die Discord-Board-Limits.")
        return zone, events

    def _apply(self, payload: dict, prepared: dict[str, tuple[ZoneInfo, tuple[Event, ...]]]) -> None:
        self._regions = prepared
        self.zone, self.events = prepared[self.region_id]
        self.verified_at = payload["updatedAt"]
        self._payload = payload
        self.available = True

    def for_region(self, region_id: str) -> "Schedule":
        if not self.available:
            raise RuntimeError("Keine gültigen Shugo-Daten verfügbar.")
        if region_id not in self._regions:
            raise ValueError("Für diese Region sind keine Shugo-Zeitpläne verfügbar.")
        if region_id == self.region_id:
            return self
        selected = copy(self)
        selected.region_id = region_id
        selected.zone, selected.events = self._regions[region_id]
        return selected

    async def refresh(self, session: aiohttp.ClientSession) -> None:
        try:
            async with session.get(SOURCE_URL, timeout=aiohttp.ClientTimeout(total=15)) as response:
                response.raise_for_status()
                payload = await response.json()
            if self.available and payload == self._payload and self.cache_path.exists():
                return
            prepared = self._prepare(payload)
            await asyncio.to_thread(write_json, self.cache_path, payload)
            self._apply(payload, prepared)
            logger.info("Shugo-Zeitplandaten aktualisiert: %s", self.verified_at)
        except (aiohttp.ClientError, TimeoutError, OSError, ValueError, KeyError, TypeError) as error:
            logger.warning("Shugo-Aktualisierung fehlgeschlagen; letzte gültige Kopie bleibt aktiv: %s", error)
            if not self.available:
                raise RuntimeError("Keine gültigen Shugo-Daten online oder lokal verfügbar.") from error

    def occurrences(self, now: datetime) -> list[Occurrence]:
        if now.tzinfo is None or now.utcoffset() is None:
            raise ValueError("now muss eine explizite Zeitzone haben.")
        if not self.available:
            raise RuntimeError("Keine gültigen Shugo-Daten verfügbar.")
        now = now.astimezone(UTC)
        result = []
        for event in self.events:
            today = now.astimezone(event.zone).date()
            candidates = (
                min(
                    ((start, end) for start, end in event.slots(today + timedelta(days=offset))
                     if start >= now or end > now),
                    default=None,
                )
                for offset in range(-1, 8)
            )
            start, end = next(candidate for candidate in candidates if candidate is not None)
            result.append(Occurrence(
                event_id=event.event_id, name=event.name, emoji=event.emoji, kind=event.kind,
                starts_at=start, ends_at=end, active=start <= now < end,
                portal_ends_at=start + event.portal if event.portal is not None else None,
            ))
        return sorted(result, key=lambda occurrence: (occurrence.starts_at, occurrence.event_id))
