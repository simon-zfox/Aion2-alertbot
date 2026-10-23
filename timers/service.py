import asyncio
import logging
from collections.abc import Callable
from contextlib import suppress
from datetime import UTC, datetime
from time import monotonic
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from discord.types.embed import Embed as EmbedPayload

import aiohttp
import discord
from discord.ext import tasks

from timers.schedule import Schedule
from timers.store import Board, BoardStore
from timers.view import build_board


logger = logging.getLogger(__name__)


class BoardService:
    def __init__(
        self, client: discord.Client, store: BoardStore, schedule: Schedule,
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        self.client = client
        self.store = store
        self.schedule = schedule
        self.clock = clock
        self._lock = asyncio.Lock()
        self._rendered: dict[int, list["EmbedPayload"]] = {}
        self._http: aiohttp.ClientSession | None = None
        self._next_download = 0.0

    async def start(self) -> None:
        await asyncio.to_thread(self.store.initialize)
        self._http = aiohttp.ClientSession()
        try:
            await self.schedule.refresh(self._http)
            self._next_download = monotonic() + 3600
            self.update_boards.start()
        except BaseException:
            await self._http.close()
            self._http = None
            raise

    async def close(self) -> None:
        task = self.update_boards.get_task()
        self.update_boards.cancel()
        try:
            if task is not None:
                with suppress(asyncio.CancelledError):
                    await task
        finally:
            if self._http is not None:
                await self._http.close()
                self._http = None

    async def publish(self, channel: discord.TextChannel) -> discord.Message:
        async with self._lock:
            embeds = build_board(self.schedule, self.clock())
            board = await asyncio.to_thread(self.store.get, channel.id)
            if board is not None:
                try:
                    message = await channel.fetch_message(board.message_id)
                    await message.edit(embeds=embeds, allowed_mentions=discord.AllowedMentions.none())
                except discord.NotFound as error:
                    if error.code != 10008:
                        raise
                else:
                    self._rendered[channel.id] = [embed.to_dict() for embed in embeds]
                    logger.info("Timer-Board aktualisiert (/timers): Kanal %s, Nachricht %s", channel.id, message.id)
                    return message
            message = await channel.send(embeds=embeds, allowed_mentions=discord.AllowedMentions.none())
            try:
                await asyncio.to_thread(self.store.save, Board(channel.guild.id, channel.id, message.id))
            except Exception:
                # Ohne gespeicherte ID könnte der nächste Aufruf ein zweites Board anlegen.
                try:
                    await message.delete()
                except discord.HTTPException:
                    logger.exception("Nicht gespeichertes Timer-Board konnte nicht entfernt werden")
                raise
            self._rendered[channel.id] = [embed.to_dict() for embed in embeds]
            return message

    async def refresh(self) -> None:
        async with self._lock:
            boards = await asyncio.to_thread(self.store.list_all)
            live_channels = {board.channel_id for board in boards}
            self._rendered = {key: value for key, value in self._rendered.items() if key in live_channels}
            if not boards:
                return
            embeds = build_board(self.schedule, self.clock())
            payload = [embed.to_dict() for embed in embeds]
            for board in boards:
                try:
                    channel = self.client.get_channel(board.channel_id)
                    if channel is None:
                        channel = await self.client.fetch_channel(board.channel_id)
                    if not isinstance(channel, discord.TextChannel):
                        logger.warning("Timer-Kanal %s ist kein Textkanal", board.channel_id)
                        continue
                    message = await channel.fetch_message(board.message_id)
                    if self._rendered.get(board.channel_id) != payload:
                        await message.edit(embeds=embeds, allowed_mentions=discord.AllowedMentions.none())
                        self._rendered[board.channel_id] = payload
                        logger.info(
                            "Timer-Board aktualisiert (automatisch): Kanal %s, Nachricht %s",
                            board.channel_id, board.message_id,
                        )
                except discord.NotFound as error:
                    if error.code in {10003, 10008}:
                        await asyncio.to_thread(self.store.remove, board.channel_id)
                        self._rendered.pop(board.channel_id, None)
                        logger.info("Gelöschtes Timer-Board in Kanal %s entfernt", board.channel_id)
                    else:
                        logger.warning("Timer-Board %s nicht erreichbar: %s", board.channel_id, error)
                except discord.HTTPException as error:
                    logger.warning("Timer-Board %s wird später erneut versucht: %s", board.channel_id, error)
                except Exception:
                    logger.exception("Timer-Board %s konnte nicht aktualisiert werden", board.channel_id)

    @tasks.loop(seconds=60)
    async def update_boards(self) -> None:
        try:
            if self._http is not None and monotonic() >= self._next_download:
                await self.schedule.refresh(self._http)
                self._next_download = monotonic() + 3600
            await self.refresh()
        except Exception:
            logger.exception("Timer-Aktualisierung fehlgeschlagen; erneuter Versuch in 60 Sekunden")

    @update_boards.before_loop
    async def before_update(self) -> None:
        await self.client.wait_until_ready()
