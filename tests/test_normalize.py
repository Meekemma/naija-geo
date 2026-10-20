import json
from collections import Counter
from importlib.resources import files

import pytest

from naija_geo.normalize import normalize, normalize_state


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("Ikeja", "ikeja"),
        ("IKEJA", "ikeja"),
        ("  Ikeja  ", "ikeja"),
        ("Ifako-Ijaiye", "ifako ijaiye"),
        ("Ifako/Ijaiye", "ifako ijaiye"),
        ("Ifako Ijaiye", "ifako ijaiye"),
        ("ifako_ijaiye", "ifako ijaiye"),
        ("Ifako - Ijaiye", "ifako ijaiye"),
        ("Ifako  /  Ijaiye", "ifako ijaiye"),
        ("Isiala\tNgwa\nNorth", "isiala ngwa north"),
        ("Jama'are", "jamaare"),
        ("Jama\u2019are", "jamaare"),
        ("Jama\u02bcare", "jamaare"),
        ("Qua`an Pan", "quaan pan"),
        ("Ọ̀yọ́", "oyo"),
        ("Ìbàdàn North", "ibadan north"),
        ("-Ikeja/", "ikeja"),
        ("", ""),
        ("   ", ""),
    ],
)
def test_normalize(text: str, expected: str) -> None:
    assert normalize(text) == expected


def test_normalize_keeps_the_word_state() -> None:
    # Only state lookups drop "state"; an LGA name must come through unchanged.
    assert normalize("Lagos State") == "lagos state"


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("Lagos", "lagos"),
        ("Lagos State", "lagos"),
        ("lagos state", "lagos"),
        ("LAGOS-STATE", "lagos"),
        ("Cross River State", "cross river"),
        ("Akwa-Ibom State", "akwa ibom"),
        ("State of Osun", "osun"),
        ("state of osun", "osun"),
        ("Osun State", "osun"),
        ("Statehouse", "statehouse"),
        ("State", "state"),
        ("", ""),
    ],
)
def test_normalize_state(text: str, expected: str) -> None:
    assert normalize_state(text) == expected


# Cross-checks against the shipped data: normalization must not merge labels that should
# stay distinct, otherwise find_state() / find_lga() would become ambiguous.

DATA = files("naija_geo") / "data"


def _load(name: str) -> list[dict[str, object]]:
    data: list[dict[str, object]] = json.loads((DATA / name).read_text(encoding="utf-8"))
    return data


def _labels(record: dict[str, object]) -> list[str]:
    aliases = record["aliases"]
    assert isinstance(aliases, list)
    return [str(record["name"]), *aliases]


def test_state_labels_stay_unambiguous_after_normalization() -> None:
    owners: dict[str, set[object]] = {}
    for state in _load("states.json"):
        for label in _labels(state):
            owners.setdefault(normalize_state(label), set()).add(state["code"])
    assert {key: codes for key, codes in owners.items() if len(codes) > 1} == {}


def test_lga_labels_stay_unambiguous_within_state_after_normalization() -> None:
    owners: dict[tuple[object, str], set[object]] = {}
    for lga in _load("lgas.json"):
        for label in _labels(lga):
            owners.setdefault((lga["state"], normalize(label)), set()).add(lga["code"])
    assert {key: codes for key, codes in owners.items() if len(codes) > 1} == {}


def test_no_alias_is_redundant_after_normalization() -> None:
    redundant = []
    for state in _load("states.json"):
        keys = [normalize_state(label) for label in _labels(state)]
        redundant += [state["code"] for _, count in Counter(keys).items() if count > 1]
    for lga in _load("lgas.json"):
        keys = [normalize(label) for label in _labels(lga)]
        redundant += [lga["code"] for _, count in Counter(keys).items() if count > 1]
    assert redundant == []
