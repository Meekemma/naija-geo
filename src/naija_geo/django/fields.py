"""Form fields for picking a state and an LGA, with an optional dependent dropdown.

Both fields submit codes (``NG-LA``, ``NG-LA-11``) rather than database ids. A typical form::

    class AddressForm(StateLGAFormMixin, forms.Form):
        state = StateChoiceField()
        lga = LGAChoiceField(widget=StateLGAWidget(state_field="state"))

Include ``{{ form.media }}`` in the template for the dropdown script.
"""

from collections.abc import Iterable
from typing import TYPE_CHECKING, Any

from django import forms
from django.db.models import QuerySet

import naija_geo
from naija_geo.core import _resolve_state
from naija_geo.django.models import LGA, State

# Django's form fields are only generic in django-stubs, not at runtime.
if TYPE_CHECKING:
    _StateField = forms.ModelChoiceField[State]
    _LGAField = forms.ModelChoiceField[LGA]
else:
    _StateField = _LGAField = forms.ModelChoiceField


def _state_code(state: str | State) -> str:
    """Accept a State, a state code or a state name; raise ``KeyError`` if unknown."""
    return state.code if isinstance(state, State) else _resolve_state(state).code


class StateChoiceField(_StateField):
    """Choose a state, optionally only from some zones: ``StateChoiceField(zones=["SW"])``."""

    def __init__(self, *, zones: Iterable[str] | None = None, **kwargs: Any) -> None:
        queryset = State.objects.all()
        if zones is not None:
            codes = [naija_geo.get_zone(zone).code for zone in zones]
            queryset = queryset.filter(zone__code__in=codes)
        kwargs.setdefault("to_field_name", "code")
        kwargs.setdefault("empty_label", "Select a state")
        super().__init__(queryset=queryset, **kwargs)


class LGAChoiceField(_LGAField):
    """Choose an LGA, optionally only from one state: ``LGAChoiceField(state="NG-LA")``."""

    def __init__(self, *, state: str | State | None = None, **kwargs: Any) -> None:
        kwargs.setdefault("to_field_name", "code")
        kwargs.setdefault("empty_label", "Select an LGA")
        super().__init__(queryset=self._lga_queryset(state), **kwargs)

    def limit_to_state(self, state: str | State | None) -> None:
        """Restrict the choices to one state (or lift the restriction with ``None``)."""
        self.queryset = self._lga_queryset(state)

    @staticmethod
    def _lga_queryset(state: str | State | None) -> QuerySet[LGA]:
        queryset = LGA.objects.select_related("state")
        if state is not None:
            queryset = queryset.filter(state__code=_state_code(state))
        return queryset


class StateLGAWidget(forms.Select):
    """An LGA ``<select>`` that only shows the LGAs of the state chosen in ``state_field``.

    Each option carries its state's code, and a small script hides the rest. The state field
    must submit state codes, as ``StateChoiceField`` does. Pair it with
    ``StateLGAFormMixin`` so the choice is also checked on the server.
    """

    class Media:
        js = ["naija_geo/state_lga.js"]

    def __init__(self, state_field: str = "state", attrs: dict[str, Any] | None = None) -> None:
        super().__init__(attrs)
        self.state_field = state_field

    def get_context(self, name: str, value: Any, attrs: dict[str, Any] | None) -> dict[str, Any]:
        context = super().get_context(name, value, attrs)
        # Keep any form prefix: "address-lga" pairs with "address-state".
        prefix, separator, _ = name.rpartition("-")
        context["widget"]["attrs"]["data-naija-geo-lga"] = ""
        context["widget"]["attrs"]["data-state-field"] = f"{prefix}{separator}{self.state_field}"
        return context

    def create_option(
        self,
        name: str,
        value: Any,
        label: Any,
        selected: Any,
        index: int,
        subindex: int | None = None,
        attrs: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        option = super().create_option(name, value, label, selected, index, subindex, attrs)
        instance = getattr(value, "instance", None)
        if isinstance(instance, LGA):
            option["attrs"]["data-state"] = instance.state.code
        return option


class StateLGAFormMixin(forms.BaseForm):
    """Reject an LGA that is not in the chosen state.

    Set ``state_field_name`` and ``lga_field_name`` if your fields are not called ``state``
    and ``lga``.
    """

    state_field_name = "state"
    lga_field_name = "lga"

    def clean(self) -> dict[str, Any]:
        cleaned_data = super().clean() or {}
        state = cleaned_data.get(self.state_field_name)
        lga = cleaned_data.get(self.lga_field_name)
        if isinstance(state, State) and isinstance(lga, LGA) and lga.state_id != state.pk:
            self.add_error(
                self.lga_field_name,
                forms.ValidationError(
                    "%(lga)s is not in %(state)s.",
                    code="lga_not_in_state",
                    params={"lga": lga.name, "state": state.name},
                ),
            )
        return cleaned_data
