import pytest
from django.test import Client

from naija_geo.django.models import LGA, State, Zone

pytestmark = pytest.mark.usefixtures("loaded")


@pytest.mark.parametrize("model", ["zone", "state", "lga"])
def test_changelists_load(admin_client: Client, model: str) -> None:
    response = admin_client.get(f"/admin/naija_geo/{model}/")
    assert response.status_code == 200


@pytest.mark.parametrize(
    ("query", "expected"),
    [("ikeja", "NG-LA-11"), ("NG-LA-11", "Ikeja"), ("AMAC", "Municipal Area Council")],
)
def test_lga_search(admin_client: Client, query: str, expected: str) -> None:
    response = admin_client.get("/admin/naija_geo/lga/", {"q": query})
    assert expected in response.content.decode()


def test_state_search_by_alias(admin_client: Client) -> None:
    response = admin_client.get("/admin/naija_geo/state/", {"q": "Nassarawa"})
    assert "NG-NA" in response.content.decode()


def test_lga_filter_by_zone(admin_client: Client) -> None:
    south_west = Zone.objects.get(code="SW")
    response = admin_client.get("/admin/naija_geo/lga/", {"state__zone__id__exact": south_west.pk})
    html = response.content.decode()
    assert response.status_code == 200
    assert "Ikeja" in html
    assert "Kano Municipal" not in html


def test_adding_is_disabled(admin_client: Client) -> None:
    assert admin_client.get("/admin/naija_geo/lga/add/").status_code == 403


def test_state_page_is_view_only_and_lists_its_lgas(admin_client: Client) -> None:
    lagos = State.objects.get(code="NG-LA")
    response = admin_client.get(f"/admin/naija_geo/state/{lagos.pk}/change/")
    html = response.content.decode()
    assert response.status_code == 200
    assert "Ifako-Ijaiye" in html
    assert 'name="_save"' not in html


def test_deleting_is_disabled(admin_client: Client) -> None:
    ikeja = LGA.objects.get(code="NG-LA-11")
    assert admin_client.get(f"/admin/naija_geo/lga/{ikeja.pk}/delete/").status_code == 403
