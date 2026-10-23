import logging

import discord
from discord import app_commands

from timers.service import BoardService


logger = logging.getLogger(__name__)


def create_timers_command(service: BoardService) -> app_commands.Command:
    @app_commands.command(name="timers", description="Postet oder aktualisiert das automatische AION-2-Timer-Board.")
    @app_commands.guild_only()
    @app_commands.default_permissions(manage_guild=True)
    @app_commands.checks.has_permissions(manage_guild=True)
    async def timers(interaction: discord.Interaction) -> None:
        channel = interaction.channel
        if interaction.guild_id is None or not isinstance(channel, discord.TextChannel):
            await interaction.response.send_message(
                "Bitte /timers in einem Server-Textkanal verwenden (nicht in Threads oder DMs).",
                ephemeral=True,
            )
            return
        permissions = interaction.app_permissions
        required_permissions = {
            "view_channel": "Kanal ansehen",
            "send_messages": "Nachrichten senden",
            "embed_links": "Links einbetten",
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
        await interaction.response.defer(ephemeral=True, thinking=True)
        try:
            message = await service.publish(channel)
        except discord.Forbidden:
            text = "Kein Zugriff auf das Timer-Board. Bitte die Kanalberechtigungen des Bots prüfen."
        except discord.HTTPException:
            logger.exception("Discord-Fehler beim Veröffentlichen des Timer-Boards")
            text = "Discord konnte das Board nicht aktualisieren. Bitte später erneut versuchen."
        except Exception:
            logger.exception("Timer-Board konnte nicht veröffentlicht oder gespeichert werden")
            text = "Das Timer-Board konnte nicht dauerhaft gespeichert werden. Bitte die Bot-Logs prüfen."
        else:
            text = f"Timer-Board bereit: {message.jump_url}\nAktualisierung alle 60 Sekunden."
        await interaction.followup.send(text, ephemeral=True)

    @timers.error
    async def on_error(interaction: discord.Interaction, error: app_commands.AppCommandError) -> None:
        if isinstance(error, app_commands.MissingPermissions):
            text = "Für /timers benötigst du die Berechtigung „Server verwalten“."
        elif isinstance(error, app_commands.NoPrivateMessage):
            text = "/timers ist nur auf einem Server verfügbar."
        else:
            logger.error("Fehler bei /timers", exc_info=(type(error), error, error.__traceback__))
            text = "Das Timer-Board konnte nicht aktualisiert werden. Bitte später erneut versuchen."
        if interaction.response.is_done():
            await interaction.followup.send(text, ephemeral=True)
        else:
            await interaction.response.send_message(text, ephemeral=True)

    return timers
