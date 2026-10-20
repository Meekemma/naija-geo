from typing import Any

import pytest
from django.test import override_settings
from pytest_django import DjangoAssertNumQueries
from rest_framework.test import APIClient

from naija_geo.django.models import LGA
from naija_geo.drf.serializers import LGASerializer

pytestmark = pytest.mark.usefixtures("loaded")

BASE = "/api/locations"


@pytest.fixture
def client() -> APIClient:
    return APIClient()


def get(client: APIClient, path: str, **params: str) -> Any:
    response = client.get(f"{BASE}{path}", params)
    assert response.status_code == 200, response.content
    return response.json()


def codes(rows: list[dict[str, Any]]) -> list[str]:
    return [row["code"] for row in rows]


# Zones


def test_zones(client: APIClient) -> None:
    zones = get(client, "/zones/")
    assert isinstance(zones, list), "responses are not paginated"
    assert codes(zones) == ["NC", "NE", "NW", "SE", "SS", "SW"]


def test_zone_detail(client: APIClient) -> None:
    assert get(client, "/zones/sw/") == {"code": "SW", "name": "South West"}


# States


def test_states(client: APIClient) -> None:
    states = get(client, "/states/")
    assert len(states) == 37
    assert states[0]["name"] == "Abia"


@pytest.mark.parametrize("zone", ["SW", "sw"])
def test_states_by_zone(client: APIClient, zone: str) -> None:
    states = get(client, "/states/", zone=zone)
    assert sorted(codes(states)) == ["NG-EK", "NG-LA", "NG-OG", "NG-ON", "NG-OS", "NG-OY"]


def test_states_unknown_zone(client: APIClient) -> None:
    response = client.get(f"{BASE}/states/", {"zone": "XX"})
    assert response.status_code == 400
    assert "zone" in response.json()


def test_state_detail(client: APIClient) -> None:
    assert get(client, "/states/NG-LA/") == {
        "code": "NG-LA",
        "name": "Lagos",
        "slug": "lagos",
        "capital": "Ikeja",
        "zone": "SW",
        "aliases": [],
    }
    assert get(client, "/states/ng-la/")["code"] == "NG-LA"


def test_state_not_found(client: APIClient) -> None:
    assert client.get(f"{BASE}/states/NG-XX/").status_code == 404


def test_state_lgas(client: APIClient) -> None:
    lgas = get(client, "/states/NG-LA/lgas/")
    assert len(lgas) == 20
    assert lgas[0] == {
        "code": "NG-LA-01",
        "name": "Agege",
        "slug": "agege",
        "state": "NG-LA",
        "aliases": [],
    }
    assert len(get(client, "/states/NG-KN/lgas/")) == 44


def test_state_lgas_not_found(client: APIClient) -> None:
    assert client.get(f"{BASE}/states/NG-XX/lgas/").status_code == 404


# LGAs


def test_lgas(client: APIClient) -> None:
    assert len(get(client, "/lgas/")) == 774


@pytest.mark.parametrize("state", ["NG-LA", "Lagos", "lagos state"])
def test_lgas_by_state(client: APIClient, state: str) -> None:
    lgas = get(client, "/lgas/", state=state)
    assert len(lgas) == 20
    assert {lga["state"] for lga in lgas} == {"NG-LA"}


def test_lgas_unknown_state(client: APIClient) -> None:
    response = client.get(f"{BASE}/lgas/", {"state": "Atlantis"})
    assert response.status_code == 400
    assert "state" in response.json()


def test_lga_detail(client: APIClient) -> None:
    assert get(client, "/lgas/ng-la-11/")["name"] == "Ikeja"


def test_lga_not_found(client: APIClient) -> None:
    assert client.get(f"{BASE}/lgas/NG-LA-99/").status_code == 404


def test_search_best_match_first(client: APIClient) -> None:
    assert codes(get(client, "/lgas/", search="ikeja"))[0] == "NG-LA-11"
    names = [lga["name"] for lga in get(client, "/lgas/", search="ike")]
    assert names == ["Ikeduru", "Ikeja", "Ikenne", "Ikere"]


def test_search_uses_aliases(client: APIClient) -> None:
    assert codes(get(client, "/lgas/", search="ifako/ijaye"))[0] == "NG-LA-10"
    assert codes(get(client, "/lgas/", search="AMAC")) == ["NG-FC-06"]


def test_search_returns_every_shared_name(client: APIClient) -> None:
    assert sorted(codes(get(client, "/lgas/", search="surulere"))) == ["NG-LA-20", "NG-OY-33"]


def test_search_within_state(client: APIClient) -> None:
    assert codes(get(client, "/lgas/", search="surulere", state="Oyo")) == ["NG-OY-33"]


def test_search_no_match(client: APIClient) -> None:
    assert get(client, "/lgas/", search="zzzz") == []


def test_blank_search_is_ignored(client: APIClient) -> None:
    assert len(get(client, "/lgas/", search="  ")) == 774


# Behaviour


@pytest.mark.parametrize("path", ["/zones/", "/states/", "/lgas/", "/states/NG-LA/"])
def test_read_only(client: APIClient, path: str) -> None:
    assert client.post(f"{BASE}{path}", {}).status_code == 405
    assert client.delete(f"{BASE}{path}").status_code == 405


@pytest.mark.parametrize(
    "path", ["/states/", "/lgas/", "/lgas/?search=north", "/states/NG-LA/lgas/"]
)
def test_lists_use_few_queries(
    client: APIClient, django_assert_max_num_queries: DjangoAssertNumQueries, path: str
) -> None:
    with django_assert_max_num_queries(2):
        client.get(f"{BASE}{path}")


@override_settings(
    REST_FRAMEWORK={
        "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
        "PAGE_SIZE": 10,
        "DEFAULT_FILTER_BACKENDS": ["rest_framework.filters.SearchFilter"],
    }
)
def test_project_pagination_and_filters_do_not_apply(client: APIClient) -> None:
    assert len(get(client, "/lgas/", search="ikeja")) == 1
    assert len(get(client, "/lgas/")) == 774


def test_api_root_lists_endpoints(client: APIClient) -> None:
    assert set(get(client, "/")) == {"zones", "states", "lgas"}


def test_serializer_is_reusable() -> None:
    data = LGASerializer(LGA.objects.select_related("state").get(code="NG-LA-11")).data
    assert data == {
        "code": "NG-LA-11",
        "name": "Ikeja",
        "slug": "ikeja",
        "state": "NG-LA",
        "aliases": [],
    }
