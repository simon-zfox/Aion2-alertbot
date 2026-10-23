from dataclasses import asdict, dataclass
from pathlib import Path

from timers.json_file import read_json, write_json


@dataclass(frozen=True)
class Board:
    guild_id: int
    channel_id: int
    message_id: int


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
        for board in boards:
            if any(type(value) is not int or value <= 0 for value in asdict(board).values()):
                raise ValueError("Board-IDs müssen positive Ganzzahlen sein.")
        if len({board.channel_id for board in boards}) != len(boards):
            raise ValueError("Mehrere Boards für denselben Kanal sind nicht erlaubt.")
        if set(data) != {"boards"}:
            write_json(self.path, {"boards": [asdict(board) for board in boards]})

    def list_all(self) -> list[Board]:
        return sorted((Board(**row) for row in read_json(self.path)["boards"]),
                      key=lambda board: board.channel_id)

    def get(self, channel_id: int) -> Board | None:
        return next((board for board in self.list_all() if board.channel_id == channel_id), None)

    def save(self, board: Board) -> None:
        self._replace(board.channel_id, board)

    def remove(self, channel_id: int) -> None:
        self._replace(channel_id, None)

    def _replace(self, channel_id: int, board: Board | None) -> None:
        data = {"boards": [asdict(saved) for saved in self.list_all()
                           if saved.channel_id != channel_id]}
        if board is not None:
            data["boards"].append(asdict(board))
        write_json(self.path, data)
