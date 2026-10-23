import logging
import os
from pathlib import Path

import discord
from discord import app_commands
from dotenv import load_dotenv


@app_commands.command(name="ping", description="Antwortet mit pong.")
async def ping(interaction: discord.Interaction) -> None:
    await interaction.response.send_message("pong")


class Bot(discord.Client):
    def __init__(self, *, intents: discord.Intents) -> None:
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)
        self.tree.add_command(ping)

    async def setup_hook(self) -> None:
        await self.tree.sync()

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
