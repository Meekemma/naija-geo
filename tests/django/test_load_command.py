from io import StringIO

import pytest
from django.core.management import call_command

import naija_geo
from naija_geo.django.models import LGA, State, Zone

pytestmark = pytest.mark.django_db


def run(*args: str) -> str:
    out = StringIO()
    call_command("load_naija_geo", *args, stdout=out)
    return out.getvalue()


def test_first_run_creates_everything() -> None:
    output = run()
    assert "Zones: 6 created, 0 updated, 0 unchanged" in output
    assert "States: 37 created, 0 updated, 0 unchanged" in output
    assert "LGAs: 774 created, 0 updated, 0 unchanged" in output
    assert (Zone.objects.count(), State.objects.count(), LGA.objects.count()) == (6, 37, 774)


def test_database_matches_the_bundled_data() -> None:
    run()
    rows = {
        lga.code: (lga.name, lga.slug, lga.state.code, tuple(lga.aliases))
        for lga in LGA.objects.select_related("state")
    }
    assert rows == {
        lga.code: (lga.name, lga.slug, lga.state_code, lga.aliases) for lga in naija_geo.get_lgas()
    }
    lagos = State.objects.select_related("zone").get(code="NG-LA")
    assert (lagos.name, lagos.capital, lagos.zone.code) == ("Lagos", "Ikeja", "SW")


def test_second_run_changes_nothing() -> None:
    run()
    ids_before = dict(LGA.objects.values_list("code", "id"))
    output = run()
    assert "Zones: 0 created, 0 updated, 6 unchanged" in output
    assert "States: 0 created, 0 updated, 37 unchanged" in output
    assert "LGAs: 0 created, 0 updated, 774 unchanged" in output
    assert dict(LGA.objects.values_list("code", "id")) == ids_before


def test_edited_rows_are_restored_in_place() -> None:
    run()
    ikeja = LGA.objects.get(code="NG-LA-11")
    LGA.objects.filter(pk=ikeja.pk).update(name="Wrong", aliases=["x"])
    State.objects.filter(code="NG-LA").update(capital="Wrong")

    output = run()

    assert "States: 0 created, 1 updated, 36 unchanged" in output
    assert "LGAs: 0 created, 1 updated, 773 unchanged" in output
    restored = LGA.objects.get(code="NG-LA-11")
    assert (restored.pk, restored.name, restored.aliases) == (ikeja.pk, "Ikeja", [])
    assert State.objects.get(code="NG-LA").capital == "Ikeja"


def test_rows_missing_from_the_data_are_kept_and_reported() -> None:
    run()
    LGA.objects.create(
        code="NG-LA-99", name="Old", slug="old", state=State.objects.get(code="NG-LA")
    )
    output = run()
    assert "LGAs: 1 row(s) no longer in the data were left in place: NG-LA-99" in output
    assert LGA.objects.filter(code="NG-LA-99").exists()


def test_dry_run_saves_nothing() -> None:
    output = run("--dry-run")
    assert "LGAs: 774 created" in output
    assert "Dry run: no changes were saved." in output
    assert LGA.objects.count() == 0


def test_dry_run_reports_pending_updates() -> None:
    run()
    LGA.objects.filter(code="NG-LA-11").update(name="Wrong")
    output = run("--dry-run")
    assert "LGAs: 0 created, 1 updated, 773 unchanged" in output
    assert LGA.objects.get(code="NG-LA-11").name == "Wrong"
