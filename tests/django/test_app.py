from io import StringIO

import pytest
from django.apps import apps
from django.core.management import call_command

from naija_geo.django.models import LGA, State, Zone


def test_app_label_is_not_django() -> None:
    config = apps.get_app_config("naija_geo")
    assert config.name == "naija_geo.django"


def test_table_names() -> None:
    assert Zone._meta.db_table == "naija_geo_zone"
    assert State._meta.db_table == "naija_geo_state"
    assert LGA._meta.db_table == "naija_geo_lga"


@pytest.mark.django_db
def test_migrations_match_models() -> None:
    call_command("makemigrations", "naija_geo", "--check", "--dry-run", stdout=StringIO())


@pytest.mark.usefixtures("loaded")
def test_str_is_the_name() -> None:
    assert str(Zone.objects.get(code="SW")) == "South West"
    assert str(State.objects.get(code="NG-LA")) == "Lagos"
    assert str(LGA.objects.get(code="NG-LA-11")) == "Ikeja"
