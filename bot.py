import logging
import os
from pathlib import Path

import discord
from discord import app_commands
from dotenv import load_dotenv

from timers.command import create_timers_command
from timers.schedule import Schedule
from timers.board_service import BoardService
from timers.board_store import BoardStore


@app_commands.command(name="ping", description="Antwortet mit pong.")
async def ping(interaction: discord.Interaction) -> None:
    await interaction.response.send_message("pong")


class Bot(discord.Client):
    def __init__(self, *, intents: discord.Intents) -> None:
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)
        self.tree.add_command(ping)
        self.timer_service = BoardService(
            self,
            BoardStore(Path(__file__).resolve().parent / "data" / "local.json"),
            Schedule(),
        )
        self.tree.add_command(create_timers_command(self.timer_service))

    async def setup_hook(self) -> None:
        await self.timer_service.start()
        await self.tree.sync()

    async def close(self) -> None:
        await self.timer_service.close()
        await super().close()

    async def on_ready(self) -> None:
        logging.getLogger(__name__).info("Angemeldet als %s", self.user)


def main() -> None:
    load_dotenv(Path(__file__).with_name(".env"))
    token = os.getenv("DISCORD_TOKEN", "").strip()
    if not token:
        raise SystemExit("DISCORD_TOKEN fehlt. Bitte in .env oder als Umgebungsvariable setzen.")

    client = Bot(intents=discord.Intents.default())
    client.run(token, root_logger=True)


if __name__ == "__main__":
    main()
