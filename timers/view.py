from datetime import datetime

import discord

from timers.schedule import Occurrence, Schedule


def timestamp(value: datetime, style: str = "R") -> str:
    return f"<t:{int(value.timestamp())}:{style}>"


def describe(occurrence: Occurrence, now: datetime) -> str:
    if occurrence.active:
        text = f"🟢 **Aktiv** · Ende {timestamp(occurrence.ends_at)}"
    else:
        text = f"Start {timestamp(occurrence.starts_at)}\n{timestamp(occurrence.starts_at, 'f')}"
    if occurrence.portal_ends_at is not None:
        if occurrence.active:
            if now < occurrence.portal_ends_at:
                text += f"\n🌀 Portal offen bis {timestamp(occurrence.portal_ends_at)}"
            else:
                text += "\nPortal geschlossen · Event läuft weiter"
        else:
            duration = int((occurrence.portal_ends_at - occurrence.starts_at).total_seconds() // 60)
            text += f"\nPortal: erste {duration} Minuten"
    return text


def build_board(schedule: Schedule, now: datetime) -> list[discord.Embed]:
    occurrences = schedule.occurrences(now)
    groups = (
        ("🎪 Events", [o for o in occurrences if o.kind not in {"boss", "reset"}]),
        ("🌍 Weltbosse", [o for o in occurrences if o.kind == "boss"]),
        ("🔄 Resets", [o for o in occurrences if o.kind == "reset"]),
    )
    embeds = []
    for title, items in groups:
        embed = discord.Embed(title=title, colour=0x2B6CB0)
        for item in items:
            embed.add_field(name=f"{item.emoji} {item.name}", value=describe(item, now), inline=False)
        embeds.append(embed)
    embeds[0].title = "🕒 AION 2 – Timer-Board · Events"
    embeds[0].description = (
        f"**{schedule.local['regionId']} · {schedule.zone.key} · UTC{now.astimezone(schedule.zone):%z}**\n"
        "Je Event der laufende oder nächste Termin. Uhrzeiten in deiner Discord-Zeitzone.\n"
        "Community-Zeitpläne, keine offiziellen Garantien; nach Patches im Spiel prüfen."
    )
    embeds[1].description = "Bossgruppen laut Zeitplandaten; keine individuellen Respawn-Prognosen."
    embeds[2].set_footer(text=(
        f"Shugo-Datenstand: {schedule.verified_at} · Lokale Ergänzungen: {schedule.local['updatedAt']}\n"
        "Statusprüfung alle 60 Sekunden · Countdown durch Discord"
    ))
    return embeds
