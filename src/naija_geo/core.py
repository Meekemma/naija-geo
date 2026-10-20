"""Pure-Python lookups over the bundled data. No Django, no network, no dependencies.

``get_*`` functions look records up by code and raise ``KeyError`` for an unknown code.
``find_*`` functions look records up by name or alias and return ``None`` when nothing
matches. Wherever a ``state`` argument is accepted, it may be a state code or a state name.
"""

import json
from collections.abc import Iterable
from dataclasses import dataclass
from functools import lru_cache
from importlib.resources import files
from typing import Any, TypeVar

from naija_geo.exceptions import AmbiguousLGAError, AmbiguousStateError
from naija_geo.normalize import normalize, normalize_state
from naija_geo.types import LGA, State, Zone

_Record = TypeVar("_Record", State, LGA)


@dataclass(frozen=True)
class _Index:
    zones: tuple[Zone, ...]
    states: tuple[State, ...]
    lgas: tuple[LGA, ...]
    zone_by_code: dict[str, Zone]
    state_by_code: dict[str, State]
    lga_by_code: dict[str, LGA]
    states_by_zone: dict[str, tuple[State, ...]]
    lgas_by_state: dict[str, tuple[LGA, ...]]
    states_by_key: dict[str, tuple[State, ...]]
    lgas_by_key: dict[str, tuple[LGA, ...]]
    keys_by_lga: dict[str, tuple[str, ...]]


def _read(name: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = json.loads(
        (files("naija_geo") / "data" / name).read_text(encoding="utf-8")
    )
    return rows


def _group(pairs: Iterable[tuple[str, _Record]]) -> dict[str, tuple[_Record, ...]]:
    groups: dict[str, list[_Record]] = {}
    for key, record in pairs:
        bucket = groups.setdefault(key, [])
        if record not in bucket:
            bucket.append(record)
    return {key: tuple(records) for key, records in groups.items()}


@lru_cache(maxsize=1)
def _index() -> _Index:
    zones = tuple(Zone(code=row["code"], name=row["name"]) for row in _read("zones.json"))
    states = tuple(
        State(
            code=row["code"],
            name=row["name"],
            slug=row["slug"],
            capital=row["capital"],
            zone_code=row["zone"],
            aliases=tuple(row["aliases"]),
        )
        for row in _read("states.json")
    )
    lgas = tuple(
        LGA(
            code=row["code"],
            name=row["name"],
            slug=row["slug"],
            state_code=row["state"],
            aliases=tuple(row["aliases"]),
        )
        for row in _read("lgas.json")
    )
    return _Index(
        zones=zones,
        states=states,
        lgas=lgas,
        zone_by_code={zone.code: zone for zone in zones},
        state_by_code={state.code: state for state in states},
        lga_by_code={lga.code: lga for lga in lgas},
        states_by_zone={
            zone.code: tuple(s for s in states if s.zone_code == zone.code) for zone in zones
        },
        lgas_by_state={
            state.code: tuple(lga for lga in lgas if lga.state_code == state.code)
            for state in states
        },
        states_by_key=_group(
            (normalize_state(label), state)
            for state in states
            for label in (state.name, *state.aliases)
        ),
        lgas_by_key=_group(
            (normalize(label), lga) for lga in lgas for label in (lga.name, *lga.aliases)
        ),
        keys_by_lga={
            lga.code: tuple(normalize(label) for label in (lga.name, *lga.aliases)) for lga in lgas
        },
    )


def _code(code: str) -> str:
    return code.strip().upper()


def _resolve_state(state: str) -> State:
    """Accept a state code or name; raise ``KeyError`` if it is neither."""
    found = _index().state_by_code.get(_code(state)) or find_state(state)
    if found is None:
        raise KeyError(f"Unknown state: {state!r}")
    return found


# Zones


def get_zones() -> list[Zone]:
    """Return all six geopolitical zones."""
    return list(_index().zones)


def get_zone(code: str) -> Zone:
    """Return the zone with this code, e.g. ``"SW"``."""
    try:
        return _index().zone_by_code[_code(code)]
    except KeyError:
        raise KeyError(f"Unknown zone code: {code!r}") from None


# States


def get_states(zone: str | None = None) -> list[State]:
    """Return all 37 states (36 + FCT) ordered by name, optionally only those in ``zone``."""
    if zone is None:
        return list(_index().states)
    return list(_index().states_by_zone[get_zone(zone).code])


def get_state(code: str) -> State:
    """Return the state with this ISO 3166-2 code, e.g. ``"NG-LA"``."""
    try:
        return _index().state_by_code[_code(code)]
    except KeyError:
        raise KeyError(f"Unknown state code: {code!r}") from None


def find_state(name: str) -> State | None:
    """Return the state matching a name or alias, e.g. ``"lagos state"`` or ``"FCT"``.

    Returns ``None`` when nothing matches, and raises ``AmbiguousStateError`` if more than
    one state matches.
    """
    matches = _index().states_by_key.get(normalize_state(name), ())
    if len(matches) > 1:
        raise AmbiguousStateError(name, matches)
    return matches[0] if matches else None


# LGAs


def get_lgas(state: str | None = None) -> list[LGA]:
    """Return all 774 LGAs, or only those in ``state`` (a code or name)."""
    if state is None:
        return list(_index().lgas)
    return list(_index().lgas_by_state[_resolve_state(state).code])


def get_lga(code: str) -> LGA:
    """Return the LGA with this code, e.g. ``"NG-LA-11"``."""
    try:
        return _index().lga_by_code[_code(code)]
    except KeyError:
        raise KeyError(f"Unknown LGA code: {code!r}") from None


def find_lgas(name: str, state: str | None = None) -> list[LGA]:
    """Return every LGA matching a name or alias, optionally only in ``state``.

    Never raises for an ambiguous name; use this when several matches are acceptable.
    """
    matches = _index().lgas_by_key.get(normalize(name), ())
    if state is not None:
        state_code = _resolve_state(state).code
        matches = tuple(lga for lga in matches if lga.state_code == state_code)
    return list(matches)


def find_lga(name: str, state: str | None = None) -> LGA | None:
    """Return the LGA matching a name or alias, optionally only in ``state``.

    Returns ``None`` when nothing matches. Some names exist in more than one state (for
    example Surulere, in Lagos and Oyo); without ``state`` these raise ``AmbiguousLGAError``.
    """
    matches = find_lgas(name, state)
    if len(matches) > 1:
        raise AmbiguousLGAError(name, matches)
    return matches[0] if matches else None


def search_lgas(query: str, state: str | None = None) -> list[LGA]:
    """Return LGAs whose name or alias contains ``query``, best matches first.

    Exact matches come first, then names starting with the query, then names containing it;
    ties are ordered by name. An empty query returns an empty list. Meant for search boxes
    and autocomplete, where ``find_lgas()`` (exact matches only) is too strict.
    """
    key = normalize(query)
    if not key:
        return []
    index = _index()
    candidates = index.lgas if state is None else index.lgas_by_state[_resolve_state(state).code]
    ranked: list[tuple[int, str, LGA]] = []
    for lga in candidates:
        keys = index.keys_by_lga[lga.code]
        if key in keys:
            rank = 0
        elif any(k.startswith(key) for k in keys):
            rank = 1
        elif any(key in k for k in keys):
            rank = 2
        else:
            continue
        ranked.append((rank, lga.name.casefold(), lga))
    return [lga for _, _, lga in sorted(ranked, key=lambda item: item[:2])]
