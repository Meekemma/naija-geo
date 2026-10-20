import dataclasses

import pytest

from naija_geo.exceptions import AmbiguousLGAError, AmbiguousMatchError, AmbiguousStateError
from naija_geo.types import LGA, State, Zone

LAGOS = State(code="NG-LA", name="Lagos", slug="lagos", capital="Ikeja", zone_code="SW", aliases=())
SURULERE_LA = LGA(code="NG-LA-20", name="Surulere", slug="surulere", state_code="NG-LA")
SURULERE_OY = LGA(code="NG-OY-33", name="Surulere", slug="surulere", state_code="NG-OY")


@pytest.mark.parametrize("record", [Zone(code="SW", name="South West"), LAGOS, SURULERE_LA])
def test_records_are_frozen(record: Zone | State | LGA) -> None:
    with pytest.raises(dataclasses.FrozenInstanceError):
        record.name = "Changed"  # type: ignore[misc]


def test_records_compare_and_hash_by_value() -> None:
    copy = LGA(code="NG-LA-20", name="Surulere", slug="surulere", state_code="NG-LA")
    assert copy == SURULERE_LA
    assert {copy, SURULERE_LA, SURULERE_OY} == {SURULERE_LA, SURULERE_OY}


def test_records_use_slots() -> None:
    assert not hasattr(LAGOS, "__dict__")


def test_str_is_the_name() -> None:
    assert str(Zone(code="SW", name="South West")) == "South West"
    assert str(LAGOS) == "Lagos"
    assert f"{SURULERE_LA}" == "Surulere"


def test_aliases_default_to_empty_tuple() -> None:
    assert SURULERE_LA.aliases == ()


def test_ambiguous_lga_error() -> None:
    error = AmbiguousLGAError("surulere", [SURULERE_LA, SURULERE_OY])
    assert isinstance(error, AmbiguousMatchError)
    assert isinstance(error, LookupError)
    assert error.query == "surulere"
    assert error.candidates == (SURULERE_LA, SURULERE_OY)
    message = str(error)
    assert "Surulere (NG-LA-20)" in message
    assert "Surulere (NG-OY-33)" in message
    assert "state=" in message


def test_ambiguous_state_error() -> None:
    error = AmbiguousStateError("lagos", [LAGOS, LAGOS])
    assert isinstance(error, AmbiguousMatchError)
    assert error.candidates == (LAGOS, LAGOS)
    assert "by code" in str(error)
