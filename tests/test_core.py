import pytest

import naija_geo
from naija_geo import (
    LGA,
    AmbiguousLGAError,
    State,
    Zone,
    find_lga,
    find_lgas,
    find_state,
    get_lga,
    get_lgas,
    get_state,
    get_states,
    get_zone,
    get_zones,
    search_lgas,
)

SHARED_LGA_NAMES = {
    "Bassa": {"NG-KO", "NG-PL"},
    "Ifelodun": {"NG-KW", "NG-OS"},
    "Irepodun": {"NG-KW", "NG-OS"},
    "Nasarawa": {"NG-KN", "NG-NA"},
    "Obi": {"NG-BE", "NG-NA"},
    "Surulere": {"NG-LA", "NG-OY"},
}


# Zones


def test_get_zones() -> None:
    zones = get_zones()
    assert len(zones) == 6
    assert all(isinstance(zone, Zone) for zone in zones)


def test_get_zone() -> None:
    assert get_zone("SW") == Zone(code="SW", name="South West")
    assert get_zone(" sw ") == get_zone("SW")


def test_get_zone_unknown() -> None:
    with pytest.raises(KeyError, match="XX"):
        get_zone("XX")


# States


def test_get_states() -> None:
    states = get_states()
    assert len(states) == 37
    assert all(isinstance(state, State) for state in states)
    assert states[0].name == "Abia"


def test_get_states_by_zone() -> None:
    south_west = get_states(zone="SW")
    assert {s.name for s in south_west} == {"Ekiti", "Lagos", "Ogun", "Ondo", "Osun", "Oyo"}
    assert get_states(zone="sw") == south_west


def test_get_states_unknown_zone() -> None:
    with pytest.raises(KeyError):
        get_states(zone="XX")


def test_get_state() -> None:
    lagos = get_state("NG-LA")
    assert lagos.name == "Lagos"
    assert lagos.capital == "Ikeja"
    assert lagos.zone_code == "SW"
    assert get_state("ng-la") is lagos


def test_get_state_unknown() -> None:
    with pytest.raises(KeyError, match="NG-XX"):
        get_state("NG-XX")


@pytest.mark.parametrize(
    ("query", "code"),
    [
        ("Lagos", "NG-LA"),
        ("lagos state", "NG-LA"),
        ("LAGOS", "NG-LA"),
        ("Akwa Ibom", "NG-AK"),
        ("akwa-ibom state", "NG-AK"),
        ("Akwaibom", "NG-AK"),
        ("Cross Rivers", "NG-CR"),
        ("State of Osun", "NG-OS"),
        ("Nassarawa", "NG-NA"),
        ("FCT", "NG-FC"),
        ("Abuja", "NG-FC"),
        ("Federal Capital Territory", "NG-FC"),
        ("fct", "NG-FC"),
    ],
)
def test_find_state(query: str, code: str) -> None:
    state = find_state(query)
    assert state is not None
    assert state.code == code


@pytest.mark.parametrize("query", ["Atlantis", "", "   ", "NG-LA", "Lagoss"])
def test_find_state_no_match(query: str) -> None:
    assert find_state(query) is None


# LGAs


def test_get_lgas_all() -> None:
    lgas = get_lgas()
    assert len(lgas) == 774
    assert all(isinstance(lga, LGA) for lga in lgas)


@pytest.mark.parametrize("state", ["NG-LA", "ng-la", "Lagos", "lagos state"])
def test_get_lgas_for_state(state: str) -> None:
    lgas = get_lgas(state)
    assert len(lgas) == 20
    assert {lga.state_code for lga in lgas} == {"NG-LA"}
    assert lgas[0].name == "Agege"


def test_get_lgas_counts() -> None:
    assert len(get_lgas("NG-KN")) == 44
    assert len(get_lgas("FCT")) == 6


def test_get_lgas_unknown_state() -> None:
    with pytest.raises(KeyError, match="Atlantis"):
        get_lgas("Atlantis")


def test_get_lga() -> None:
    ikeja = get_lga("NG-LA-11")
    assert ikeja.name == "Ikeja"
    assert ikeja.state_code == "NG-LA"
    assert get_lga("ng-la-11") is ikeja


def test_get_lga_unknown() -> None:
    with pytest.raises(KeyError, match="NG-LA-99"):
        get_lga("NG-LA-99")


@pytest.mark.parametrize(
    ("query", "code"),
    [
        ("Ikeja", "NG-LA-11"),
        ("IKEJA", "NG-LA-11"),
        ("Ifako-Ijaiye", "NG-LA-10"),
        ("ifako/ijaiye", "NG-LA-10"),
        ("ifako/ijaye", "NG-LA-10"),
        ("Jamaare", "NG-BA-11"),
        ("AMAC", "NG-FC-06"),
        ("danko/wasagu", "NG-KE-19"),
        ("Obingwa", "NG-AB-09"),
    ],
)
def test_find_lga(query: str, code: str) -> None:
    lga = find_lga(query)
    assert lga is not None
    assert lga.code == code


@pytest.mark.parametrize("query", ["Atlantis", "", "   ", "NG-LA-11", "Ikejaa"])
def test_find_lga_no_match(query: str) -> None:
    assert find_lga(query) is None


@pytest.mark.parametrize("state", ["NG-LA", "Lagos", "lagos state"])
def test_find_lga_with_state(state: str) -> None:
    lga = find_lga("ikeja", state=state)
    assert lga is not None
    assert lga.code == "NG-LA-11"


def test_find_lga_wrong_state() -> None:
    assert find_lga("Ikeja", state="NG-OY") is None


def test_find_lga_unknown_state() -> None:
    with pytest.raises(KeyError):
        find_lga("Ikeja", state="Atlantis")


@pytest.mark.parametrize(("name", "state_codes"), SHARED_LGA_NAMES.items())
def test_find_lga_ambiguous(name: str, state_codes: set[str]) -> None:
    with pytest.raises(AmbiguousLGAError) as excinfo:
        find_lga(name)
    assert excinfo.value.query == name
    assert {lga.state_code for lga in excinfo.value.candidates} == state_codes


@pytest.mark.parametrize(("name", "state_codes"), SHARED_LGA_NAMES.items())
def test_find_lga_ambiguous_resolved_by_state(name: str, state_codes: set[str]) -> None:
    for state_code in state_codes:
        lga = find_lga(name, state=state_code)
        assert lga is not None
        assert lga.state_code == state_code


def test_find_lgas() -> None:
    surulere = find_lgas("surulere")
    assert {lga.state_code for lga in surulere} == {"NG-LA", "NG-OY"}
    assert find_lgas("surulere", state="Oyo") == [get_lga("NG-OY-33")]
    assert find_lgas("ikeja") == [get_lga("NG-LA-11")]
    assert find_lgas("Atlantis") == []


def test_the_nasarawa_lga_is_not_the_nasarawa_state() -> None:
    state = find_state("Nasarawa")
    assert state is not None
    assert state.code == "NG-NA"
    assert len(find_lgas("Nasarawa")) == 2


# Search


def test_search_lgas_exact_match_first() -> None:
    results = search_lgas("ikeja")
    assert results[0].code == "NG-LA-11"


def test_search_lgas_partial() -> None:
    # Equal-ranked matches are ordered by name.
    assert [lga.name for lga in search_lgas("ike")] == ["Ikeduru", "Ikeja", "Ikenne", "Ikere"]


def test_search_lgas_ranks_prefix_before_contains() -> None:
    names = [lga.name for lga in search_lgas("aba")]
    assert names.index("Aba North") < names.index("Ikot Abasi")


def test_search_lgas_matches_aliases() -> None:
    assert [lga.code for lga in search_lgas("amac")] == ["NG-FC-06"]
    assert search_lgas("ifako/ijaye")[0].code == "NG-LA-10"


def test_search_lgas_returns_every_shared_name() -> None:
    assert {lga.state_code for lga in search_lgas("surulere")} == {"NG-LA", "NG-OY"}


def test_search_lgas_within_state() -> None:
    results = search_lgas("north", state="Abia")
    assert [lga.name for lga in results] == ["Aba North", "Isiala Ngwa North", "Umuahia North"]


@pytest.mark.parametrize("query", ["", "   ", "-", "zzzz"])
def test_search_lgas_no_results(query: str) -> None:
    assert search_lgas(query) == []


def test_search_lgas_unknown_state() -> None:
    with pytest.raises(KeyError):
        search_lgas("ikeja", state="Atlantis")


# Caching and safety


def test_returned_lists_are_copies() -> None:
    get_states().clear()
    get_lgas("NG-LA").clear()
    assert len(get_states()) == 37
    assert len(get_lgas("NG-LA")) == 20


def test_lookups_return_the_cached_records() -> None:
    assert find_state("Lagos") is get_state("NG-LA")
    assert find_lga("Ikeja") is get_lga("NG-LA-11")
    assert get_lgas("NG-LA")[10] is get_lga("NG-LA-11")


def test_every_reference_resolves() -> None:
    for state in get_states():
        assert get_zone(state.zone_code).code == state.zone_code
    for lga in get_lgas():
        assert get_state(lga.state_code).code == lga.state_code


def test_public_api() -> None:
    assert set(naija_geo.__all__) == {
        "LGA",
        "AmbiguousLGAError",
        "AmbiguousMatchError",
        "AmbiguousStateError",
        "State",
        "Zone",
        "find_lga",
        "find_lgas",
        "find_state",
        "get_lga",
        "get_lgas",
        "get_state",
        "get_states",
        "get_zone",
        "get_zones",
        "search_lgas",
    }
