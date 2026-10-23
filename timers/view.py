from datetime import datetime

import discord

from timers.schedule import Occurrence, Schedule


def timestamp(value: datetime, style: str = "R") -> str:
    return f"<t:{int(value.timestamp())}:{style}>"


def describe(occurrence: Occurrence, now: datetime) -> str:
    if occurrence.active:
        text = f"🟢 **Aktiv** · Ende {timestamp(occurrence.ends_at)}"
    else:
        text = f"Start {timestamp(occurrence.starts_at)} · {timestamp(occurrence.starts_at, 'f')}"
    if occurrence.portal_ends_at is None:
        return text
    if not occurrence.active:
        duration = int((occurrence.portal_ends_at - occurrence.starts_at).total_seconds() // 60)
        text += f" · Portal: erste {duration} Minuten"
    elif now < occurrence.portal_ends_at:
        text += f" · 🌀 Portal offen bis {timestamp(occurrence.portal_ends_at)}"
    else:
        text += " · Portal geschlossen"
    return text


def build_board(schedule: Schedule, now: datetime) -> discord.ui.LayoutView:
    occurrences = schedule.occurrences(now)
    groups = (
        ("🎪 Events", [o for o in occurrences if o.kind not in {"boss", "reset"}]),
        ("🌍 Weltbosse", [o for o in occurrences if o.kind == "boss"]),
        ("🔄 Resets", [o for o in occurrences if o.kind == "reset"]),
    )
    container = discord.ui.Container(
        discord.ui.TextDisplay(
            "**🕒 AION 2 – Timer-Board**\n"
            f"-# {schedule.region_id} · {schedule.zone.key} · UTC{now.astimezone(schedule.zone):%z}"
            " · Zeiten in deiner Discord-Zeitzone"
        ),
        accent_colour=0x2B6CB0,
    )
    for title, items in groups:
        rows = [f"{item.emoji} **{item.name}** · {describe(item, now)}" for item in items]
        container.add_item(discord.ui.TextDisplay("\n".join([f"### {title}", *rows])))
    container.add_item(discord.ui.TextDisplay(
        f"-# Shugo: {schedule.verified_at} · Statusprüfung alle 60 Sekunden · Countdown durch Discord\n"
        "-# Community-Zeitpläne; nach Patches im Spiel prüfen. Bossgruppen, keine Respawn-Prognosen."
    ))
    view = discord.ui.LayoutView(timeout=None)
    view.add_item(container)
    return view
