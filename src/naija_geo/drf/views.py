"""Read-only API views. Responses are not paginated, because the dataset is small.

Project-wide filter backends are switched off here so they cannot reinterpret the
``zone``, ``state`` and ``search`` query parameters. Permissions follow the project's
``DEFAULT_PERMISSION_CLASSES``.
"""

from typing import TYPE_CHECKING, Any

from django.db.models import Case, IntegerField, QuerySet, Value, When
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.request import Request
from rest_framework.response import Response

import naija_geo
from naija_geo.core import _resolve_state
from naija_geo.django.models import LGA, State, Zone
from naija_geo.drf.serializers import LGASerializer, StateSerializer, ZoneSerializer

# DRF's viewsets are only generic in djangorestframework-stubs, not at runtime.
if TYPE_CHECKING:
    _ZoneViewSet = viewsets.ReadOnlyModelViewSet[Zone]
    _StateViewSet = viewsets.ReadOnlyModelViewSet[State]
    _LGAViewSet = viewsets.ReadOnlyModelViewSet[LGA]
else:
    _ZoneViewSet = _StateViewSet = _LGAViewSet = viewsets.ReadOnlyModelViewSet


class _CodeLookupMixin:
    """Look records up by code, case-insensitively: ``/states/ng-la/`` works."""

    lookup_field = "code"
    kwargs: dict[str, Any]

    def get_object(self) -> Any:
        self.kwargs[self.lookup_field] = self.kwargs[self.lookup_field].upper()
        return super().get_object()  # type: ignore[misc]


class ZoneViewSet(_CodeLookupMixin, _ZoneViewSet):
    """``GET /zones/`` and ``GET /zones/{code}/``."""

    queryset = Zone.objects.all()
    serializer_class = ZoneSerializer
    pagination_class = None
    filter_backends = []


class StateViewSet(_CodeLookupMixin, _StateViewSet):
    """``GET /states/?zone=SW``, ``GET /states/{code}/`` and ``GET /states/{code}/lgas/``."""

    serializer_class = StateSerializer
    pagination_class = None
    filter_backends = []

    def get_queryset(self) -> QuerySet[State]:
        queryset = State.objects.select_related("zone")
        zone = self.request.query_params.get("zone")
        if self.action == "list" and zone:
            try:
                queryset = queryset.filter(zone__code=naija_geo.get_zone(zone).code)
            except KeyError:
                raise ValidationError({"zone": [f"Unknown zone code: {zone!r}."]}) from None
        return queryset

    @action(detail=True, serializer_class=LGASerializer)
    def lgas(self, request: Request, code: str | None = None) -> Response:
        """The LGAs in one state, for cascading dropdowns."""
        state = self.get_object()
        return Response(LGASerializer(state.lgas.select_related("state"), many=True).data)


class LGAViewSet(_CodeLookupMixin, _LGAViewSet):
    """``GET /lgas/?state=NG-LA&search=ikeja`` and ``GET /lgas/{code}/``.

    ``state`` accepts a code or a name. ``search`` matches names and aliases with the same
    rules as ``naija_geo.search_lgas()``, and results are ordered best match first.
    """

    serializer_class = LGASerializer
    pagination_class = None
    filter_backends = []

    def get_queryset(self) -> QuerySet[LGA]:
        queryset = LGA.objects.select_related("state")
        if self.action != "list":
            return queryset

        state = self.request.query_params.get("state")
        state_code = None
        if state:
            try:
                state_code = _resolve_state(state).code
            except KeyError:
                raise ValidationError({"state": [f"Unknown state: {state!r}."]}) from None

        search = self.request.query_params.get("search", "").strip()
        if search:
            codes = [lga.code for lga in naija_geo.search_lgas(search, state=state_code)]
            if not codes:
                return queryset.none()
            best_first = Case(
                *[When(code=code, then=Value(rank)) for rank, code in enumerate(codes)],
                output_field=IntegerField(),
            )
            return queryset.filter(code__in=codes).order_by(best_first)

        if state_code:
            queryset = queryset.filter(state__code=state_code)
        return queryset
