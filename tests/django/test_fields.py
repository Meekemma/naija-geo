from __future__ import annotations

from typing import Any

import pytest
from django import forms
from django.db.models import QuerySet
from pytest_django import DjangoAssertNumQueries

from naija_geo.django.fields import (
    LGAChoiceField,
    StateChoiceField,
    StateLGAFormMixin,
    StateLGAWidget,
)
from naija_geo.django.models import LGA, State

pytestmark = pytest.mark.usefixtures("loaded")


def choices(field: forms.ModelChoiceField[Any]) -> QuerySet[Any]:
    assert field.queryset is not None
    return field.queryset


class AddressForm(StateLGAFormMixin, forms.Form):
    state = StateChoiceField()
    lga = LGAChoiceField(widget=StateLGAWidget(state_field="state"))


# StateChoiceField


def test_state_field_offers_every_state() -> None:
    assert choices(StateChoiceField()).count() == 37


def test_state_field_limited_to_zones() -> None:
    field = StateChoiceField(zones=["SW", "se"])
    assert choices(field).count() == 11
    assert set(choices(field).values_list("zone__code", flat=True)) == {"SW", "SE"}


def test_state_field_unknown_zone() -> None:
    with pytest.raises(KeyError):
        StateChoiceField(zones=["XX"])


def test_state_field_cleans_codes() -> None:
    assert StateChoiceField().clean("NG-LA") == State.objects.get(code="NG-LA")
    with pytest.raises(forms.ValidationError):
        StateChoiceField().clean("NG-XX")


# LGAChoiceField


def test_lga_field_offers_every_lga() -> None:
    assert choices(LGAChoiceField()).count() == 774


@pytest.mark.parametrize("state", ["NG-LA", "Lagos", "lagos state"])
def test_lga_field_limited_to_state(state: str) -> None:
    field = LGAChoiceField(state=state)
    assert choices(field).count() == 20
    assert field.clean("NG-LA-11").name == "Ikeja"
    with pytest.raises(forms.ValidationError):
        field.clean("NG-OY-33")


def test_lga_field_accepts_a_state_instance() -> None:
    field = LGAChoiceField(state=State.objects.get(code="NG-KN"))
    assert choices(field).count() == 44


def test_lga_field_limit_to_state() -> None:
    field = LGAChoiceField()
    field.limit_to_state("NG-FC")
    assert choices(field).count() == 6
    field.limit_to_state(None)
    assert choices(field).count() == 774


def test_lga_field_unknown_state() -> None:
    with pytest.raises(KeyError):
        LGAChoiceField(state="Atlantis")


# StateLGAWidget


def test_widget_links_to_the_state_field() -> None:
    html = str(AddressForm()["lga"])
    assert "data-naija-geo-lga" in html
    assert 'data-state-field="state"' in html
    assert 'value="NG-LA-11" data-state="NG-LA"' in html


def test_widget_keeps_the_form_prefix() -> None:
    html = str(AddressForm(prefix="home")["lga"])
    assert 'data-state-field="home-state"' in html


def test_widget_ships_its_script() -> None:
    assert "naija_geo/state_lga.js" in str(AddressForm().media)


def test_widget_renders_without_extra_queries(
    django_assert_max_num_queries: DjangoAssertNumQueries,
) -> None:
    form = AddressForm()
    with django_assert_max_num_queries(1):
        str(form["lga"])


# StateLGAFormMixin


def bound(**data: Any) -> AddressForm:
    return AddressForm(data=data)


def test_matching_state_and_lga_are_valid() -> None:
    form = bound(state="NG-LA", lga="NG-LA-11")
    assert form.is_valid(), form.errors
    assert form.cleaned_data["lga"] == LGA.objects.get(code="NG-LA-11")


def test_lga_from_another_state_is_rejected() -> None:
    form = bound(state="NG-LA", lga="NG-OY-33")
    assert not form.is_valid()
    assert form.errors.as_data()["lga"][0].code == "lga_not_in_state"
    assert "Surulere is not in Lagos." in form.errors["lga"]


def test_custom_field_names() -> None:
    class Form(StateLGAFormMixin, forms.Form):
        state_field_name = "home_state"
        lga_field_name = "home_lga"
        home_state = StateChoiceField()
        home_lga = LGAChoiceField()

    assert not Form(data={"home_state": "NG-LA", "home_lga": "NG-OY-33"}).is_valid()
    assert Form(data={"home_state": "NG-OY", "home_lga": "NG-OY-33"}).is_valid()
