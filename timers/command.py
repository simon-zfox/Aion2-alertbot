import logging

import discord
from discord import app_commands

from timers.board_service import BoardService
from timers.config import DEFAULT_REGION, DEFAULT_SERVER, REGIONS, resolve_config, server_catalog


logger = logging.getLogger(__name__)


def create_timers_command(service: BoardService) -> app_commands.Command:
    @app_commands.command(name="timers", description="Erstellt ein neues automatisches AION-2-Timer-Board.")
    @app_commands.guild_only()
    @app_commands.default_permissions(manage_guild=True)
    @app_commands.checks.has_permissions(manage_guild=True)
    @app_commands.describe(region="Spielregion (Standard: EU)", server="Spielserver (Standard: Azphel)")
    @app_commands.choices(region=[
        app_commands.Choice(name=label, value=key) for key, (label, _) in REGIONS.items()
    ])
    async def timers(
        interaction: discord.Interaction, region: str = DEFAULT_REGION, server: str = DEFAULT_SERVER,
    ) -> None:
        channel = interaction.channel
        if not isinstance(channel, discord.TextChannel):
            await interaction.response.send_message(
                "Bitte /timers in einem Server-Textkanal verwenden (nicht in Threads oder DMs).",
                ephemeral=True,
            )
            return
        permissions = interaction.app_permissions
        required_permissions = {
            "view_channel": "Kanal ansehen",
            "send_messages": "Nachrichten senden",
            "read_message_history": "Nachrichtenverlauf anzeigen",
        }
        missing_permissions = [
            label for name, label in required_permissions.items()
            if not getattr(permissions, name)
        ]
        if missing_permissions:
            await interaction.response.send_message(
                "Dem Bot fehlen in diesem Kanal: " + ", ".join(missing_permissions) + ".\n"
                "Bitte unter **Kanal bearbeiten → Berechtigungen** für die Bot-Rolle erlauben. "
                "Explizite Kanal-Verbote überschreiben die Serverrolle.",
                ephemeral=True,
            )
            return
        try:
            region, server = resolve_config(region, server)
        except ValueError as error:
            await interaction.response.send_message(str(error), ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True, thinking=True)
        try:
            message = await service.publish(channel, region, server)
        except ValueError as error:
            text = str(error)
        except discord.Forbidden:
            logger.exception("Kein Zugriff auf das Timer-Board")
            text = "Kein Zugriff auf das Timer-Board. Bitte die Kanalberechtigungen des Bots prüfen."
        except discord.HTTPException:
            logger.exception("Discord-Fehler beim Veröffentlichen des Timer-Boards")
            text = "Discord konnte das Board nicht aktualisieren. Bitte später erneut versuchen."
        except Exception:
            logger.exception("Timer-Board konnte nicht veröffentlicht oder gespeichert werden")
            text = "Das Timer-Board konnte nicht dauerhaft gespeichert werden. Bitte die Bot-Logs prüfen."
        else:
            text = (f"Timer-Board erstellt: {message.jump_url}\n"
                    f"{region.upper()} · {server} · Aktualisierung alle 60 Sekunden.")
        await interaction.followup.send(text, ephemeral=True)

    @timers.autocomplete("server")
    async def complete_server(interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
        region = getattr(interaction.namespace, "region", None) or DEFAULT_REGION
        names = server_catalog().get(region, {}).values()
        return [app_commands.Choice(name=name, value=name)
                for name in names if current.casefold() in name.casefold()][:25]

    timers.error(on_error)
    return timers


async def on_error(interaction: discord.Interaction, error: app_commands.AppCommandError) -> None:
    if isinstance(error, app_commands.MissingPermissions):
        text = "Für diesen Befehl benötigst du die Berechtigung „Server verwalten“."
    elif isinstance(error, app_commands.NoPrivateMessage):
        text = "Dieser Befehl ist nur auf einem Server verfügbar."
    else:
        logger.error("Fehler beim Timer-Befehl", exc_info=(type(error), error, error.__traceback__))
        text = "Der Timer-Befehl konnte nicht ausgeführt werden. Bitte später erneut versuchen."
    if interaction.response.is_done():
        await interaction.followup.send(text, ephemeral=True)
    else:
        await interaction.response.send_message(text, ephemeral=True)
