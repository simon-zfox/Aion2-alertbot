from functools import lru_cache

from timers.json_file import DATA_DIRECTORY, read_json


DEFAULT_REGION = "eu"
DEFAULT_SERVER = "Azphel"
REGIONS = {
    "eu": ("Europa", "global-eu"),
    "nae": ("Nordamerika Ost", "global-nae"),
    "naw": ("Nordamerika West", "global-naw"),
    "sa": ("Südamerika", "global-sa"),
    "as": ("Asien", "global-as"),
    "tw": ("Taiwan", "tw"),
}


@lru_cache(maxsize=1)
def server_catalog() -> dict[str, dict[str, str]]:
    payload = read_json(DATA_DIRECTORY / "servers.json")
    catalog = {}
    for region in REGIONS:
        names = {}
        ids = set()
        for server in payload["regions"][region]["servers"]:
            name = server["name"]
            server_id = server["id"]
            if not isinstance(name, str) or not name.strip() or len(name) > 100:
                raise ValueError("Ungültiger Servername in der Serverliste.")
            if type(server_id) is not int or server_id <= 0 or server_id in ids or name.casefold() in names:
                raise ValueError("Ungültiger oder doppelter Server in der Serverliste.")
            names[name.casefold()] = name
            ids.add(server_id)
        if not names:
            raise ValueError("Leere Serverliste.")
        catalog[region] = names
    return catalog


def resolve_config(region: str = DEFAULT_REGION, server: str = DEFAULT_SERVER) -> tuple[str, str]:
    region = region.strip().lower()
    if region not in REGIONS:
        raise ValueError("Unbekannte Region. Bitte eine Region aus der Auswahl verwenden.")
    name = server_catalog()[region].get(server.strip().casefold())
    if name is None:
        raise ValueError(
            f"Server „{server}“ ist für {REGIONS[region][0]} nicht verfügbar. "
            "Bitte einen Server aus der Autovervollständigung angeben."
        )
    return region, name
