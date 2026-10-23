from dataclasses import asdict, dataclass
from pathlib import Path

from timers.config import DEFAULT_REGION, DEFAULT_SERVER, resolve_config
from timers.json_file import read_json, write_json


@dataclass(frozen=True)
class Board:
    guild_id: int
    channel_id: int
    message_id: int
    region: str = DEFAULT_REGION
    server: str = DEFAULT_SERVER

    def __post_init__(self) -> None:
        if any(type(value) is not int or value <= 0
               for value in (self.guild_id, self.channel_id, self.message_id)):
            raise ValueError("Board-IDs müssen positive Ganzzahlen sein.")
        region, server = resolve_config(self.region, self.server)
        object.__setattr__(self, "region", region)
        object.__setattr__(self, "server", server)


class BoardStore:
    def __init__(self, path: Path) -> None:
        self.path = path

    def initialize(self) -> None:
        try:
            data = read_json(self.path)
        except FileNotFoundError:
            write_json(self.path, {"boards": []})
            return
        boards = [Board(**row) for row in data["boards"]]
        if len({board.message_id for board in boards}) != len(boards):
            raise ValueError("Doppelte Board-Nachrichten sind nicht erlaubt.")
        normalized = {"boards": [asdict(board) for board in boards]}
        if data != normalized:
            write_json(self.path, normalized)

    def list_all(self) -> list[Board]:
        return sorted((Board(**row) for row in read_json(self.path)["boards"]),
                      key=lambda board: board.message_id)

    def get(self, message_id: int) -> Board | None:
        return next((board for board in self.list_all() if board.message_id == message_id), None)

    def save(self, board: Board) -> None:
        self._replace(board.message_id, board)

    def remove(self, message_id: int) -> None:
        self._replace(message_id, None)

    def _replace(self, message_id: int, board: Board | None) -> None:
        data = {"boards": [asdict(saved) for saved in self.list_all()
                           if saved.message_id != message_id]}
        if board is not None:
            data["boards"].append(asdict(board))
        write_json(self.path, data)
