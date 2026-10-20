"""Checks on the canonical JSON data itself, independent of the lookup code."""

import json
import re
from collections import Counter
from importlib.resources import files
from typing import Any

import pytest

DATA = files("naija_geo") / "data"

ZONE_CODES = {"NC", "NE", "NW", "SE", "SS", "SW"}

STATES_PER_ZONE = {"NC": 7, "NE": 6, "NW": 7, "SE": 5, "SS": 6, "SW": 6}

# Official LGA count per state (Constitution of the Federal Republic of Nigeria 1999,
# First Schedule, Part I; FCT area councils from Part II).
LGAS_PER_STATE = {
    "NG-AB": 17, "NG-AD": 21, "NG-AK": 31, "NG-AN": 21, "NG-BA": 20, "NG-BY": 8,
    "NG-BE": 23, "NG-BO": 27, "NG-CR": 18, "NG-DE": 25, "NG-EB": 13, "NG-ED": 18,
    "NG-EK": 16, "NG-EN": 17, "NG-FC": 6, "NG-GO": 11, "NG-IM": 27, "NG-JI": 27,
    "NG-KD": 23, "NG-KN": 44, "NG-KT": 34, "NG-KE": 21, "NG-KO": 21, "NG-KW": 16,
    "NG-LA": 20, "NG-NA": 13, "NG-NI": 25, "NG-OG": 20, "NG-ON": 18, "NG-OS": 30,
    "NG-OY": 33, "NG-PL": 17, "NG-RI": 23, "NG-SO": 23, "NG-TA": 16, "NG-YO": 17,
    "NG-ZA": 14,
}  # fmt: skip

SLUG_RE = re.compile(r"[a-z0-9]+(-[a-z0-9]+)*")


def load(name: str) -> list[dict[str, Any]]:
    data: list[dict[str, Any]] = json.loads((DATA / name).read_text(encoding="utf-8"))
    return data


def match_key(name: str) -> str:
    # Rough stand-in for normalize.py, so these checks do not depend on the code under test:
    # case-insensitive, with "-", "/" and whitespace treated as equivalent.
    return " ".join(re.split(r"[\s/-]+", name.casefold())).strip()


def duplicates(values: list[str]) -> list[str]:
    return [value for value, count in Counter(values).items() if count > 1]


@pytest.fixture(scope="module")
def zones() -> list[dict[str, Any]]:
    return load("zones.json")


@pytest.fixture(scope="module")
def states() -> list[dict[str, Any]]:
    return load("states.json")


@pytest.fixture(scope="module")
def lgas() -> list[dict[str, Any]]:
    if not (DATA / "lgas.json").is_file():
        pytest.skip("lgas.json not compiled yet")
    return load("lgas.json")


# Zones


def test_zone_count(zones: list[dict[str, Any]]) -> None:
    assert len(zones) == 6


def test_zone_fields(zones: list[dict[str, Any]]) -> None:
    for zone in zones:
        assert set(zone) == {"code", "name"}, zone
        assert isinstance(zone["name"], str) and zone["name"].strip(), zone


def test_zone_codes(zones: list[dict[str, Any]]) -> None:
    codes = [zone["code"] for zone in zones]
    assert duplicates(codes) == []
    assert set(codes) == ZONE_CODES


def test_zone_names_unique(zones: list[dict[str, Any]]) -> None:
    assert duplicates([zone["name"] for zone in zones]) == []


# States


def test_state_count(states: list[dict[str, Any]]) -> None:
    assert len(states) == 37


def test_state_fields(states: list[dict[str, Any]]) -> None:
    for state in states:
        assert set(state) == {"code", "name", "slug", "capital", "zone", "aliases"}, state
        for key in ("code", "name", "slug", "capital", "zone"):
            assert isinstance(state[key], str) and state[key].strip(), (key, state)
        assert isinstance(state["aliases"], list), state
        assert all(isinstance(a, str) and a.strip() for a in state["aliases"]), state


def test_state_code_format(states: list[dict[str, Any]]) -> None:
    bad = [s["code"] for s in states if not re.fullmatch(r"NG-[A-Z]{2}", s["code"])]
    assert bad == []


def test_state_slug_format(states: list[dict[str, Any]]) -> None:
    bad = [s["slug"] for s in states if not SLUG_RE.fullmatch(s["slug"])]
    assert bad == []


@pytest.mark.parametrize("key", ["code", "name", "slug"])
def test_state_values_unique(states: list[dict[str, Any]], key: str) -> None:
    assert duplicates([state[key] for state in states]) == []


def test_state_zone_references(states: list[dict[str, Any]], zones: list[dict[str, Any]]) -> None:
    zone_codes = {zone["code"] for zone in zones}
    assert [s["code"] for s in states if s["zone"] not in zone_codes] == []


def test_states_per_zone(states: list[dict[str, Any]]) -> None:
    assert Counter(state["zone"] for state in states) == STATES_PER_ZONE


def test_state_names_and_aliases_unambiguous(states: list[dict[str, Any]]) -> None:
    # Every name and alias must point to exactly one state, or find_state() is ambiguous.
    owners: dict[str, set[str]] = {}
    for state in states:
        for label in [state["name"], *state["aliases"]]:
            owners.setdefault(match_key(label), set()).add(state["code"])
    assert {key: codes for key, codes in owners.items() if len(codes) > 1} == {}


def test_state_aliases_not_redundant(states: list[dict[str, Any]]) -> None:
    for state in states:
        keys = [match_key(label) for label in [state["name"], *state["aliases"]]]
        assert duplicates(keys) == [], state["code"]


# LGAs


def test_official_lga_table_sums_to_774() -> None:
    assert sum(LGAS_PER_STATE.values()) == 774
    assert len(LGAS_PER_STATE) == 37


def test_lga_table_covers_every_state(states: list[dict[str, Any]]) -> None:
    assert set(LGAS_PER_STATE) == {state["code"] for state in states}


def test_lga_count(lgas: list[dict[str, Any]]) -> None:
    assert len(lgas) == 774


def test_lga_fields(lgas: list[dict[str, Any]]) -> None:
    for lga in lgas:
        assert set(lga) == {"code", "name", "slug", "state", "aliases"}, lga
        for key in ("code", "name", "slug", "state"):
            assert isinstance(lga[key], str) and lga[key].strip(), (key, lga)
        assert isinstance(lga["aliases"], list), lga
        assert all(isinstance(a, str) and a.strip() for a in lga["aliases"]), lga


def test_lga_state_references(lgas: list[dict[str, Any]], states: list[dict[str, Any]]) -> None:
    state_codes = {state["code"] for state in states}
    assert [lga["code"] for lga in lgas if lga["state"] not in state_codes] == []


def test_lgas_per_state(lgas: list[dict[str, Any]]) -> None:
    assert dict(Counter(lga["state"] for lga in lgas)) == LGAS_PER_STATE


def test_lga_code_format(lgas: list[dict[str, Any]]) -> None:
    bad = [
        lga["code"]
        for lga in lgas
        if not re.fullmatch(r"NG-[A-Z]{2}-\d{2}", lga["code"])
        or not lga["code"].startswith(lga["state"] + "-")
    ]
    assert bad == []


def test_lga_codes_unique(lgas: list[dict[str, Any]]) -> None:
    assert duplicates([lga["code"] for lga in lgas]) == []


def test_lga_codes_contiguous_per_state(lgas: list[dict[str, Any]]) -> None:
    # Codes are never reused or renumbered, so each state's sequence runs 01..N with no gaps.
    by_state: dict[str, list[int]] = {}
    for lga in lgas:
        by_state.setdefault(lga["state"], []).append(int(lga["code"][-2:]))
    for state, numbers in by_state.items():
        assert sorted(numbers) == list(range(1, len(numbers) + 1)), state


def test_lga_codes_alphabetical_at_v1(lgas: list[dict[str, Any]]) -> None:
    # v1 assigns codes alphabetically within each state. Once an LGA is appended after v1,
    # restrict this check to the original v1 codes.
    by_state: dict[str, list[dict[str, Any]]] = {}
    for lga in lgas:
        by_state.setdefault(lga["state"], []).append(lga)
    for state, items in by_state.items():
        by_code = [lga["name"] for lga in sorted(items, key=lambda lga: lga["code"])]
        assert by_code == sorted(by_code, key=str.casefold), state


def test_lga_slug_format(lgas: list[dict[str, Any]]) -> None:
    assert [lga["slug"] for lga in lgas if not SLUG_RE.fullmatch(lga["slug"])] == []


@pytest.mark.parametrize("key", ["slug", "name"])
def test_lga_values_unique_within_state(lgas: list[dict[str, Any]], key: str) -> None:
    assert duplicates([f"{lga['state']}:{lga[key]}" for lga in lgas]) == []


def test_lga_aliases_unambiguous_within_state(lgas: list[dict[str, Any]]) -> None:
    # Within a state, every name and alias must point to exactly one LGA.
    owners: dict[tuple[str, str], set[str]] = {}
    for lga in lgas:
        for label in [lga["name"], *lga["aliases"]]:
            owners.setdefault((lga["state"], match_key(label)), set()).add(lga["code"])
    assert {key: codes for key, codes in owners.items() if len(codes) > 1} == {}


def test_lga_aliases_not_redundant(lgas: list[dict[str, Any]]) -> None:
    for lga in lgas:
        keys = [match_key(label) for label in [lga["name"], *lga["aliases"]]]
        assert duplicates(keys) == [], lga["code"]
