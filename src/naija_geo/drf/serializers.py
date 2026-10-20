"""Read-only serializers. Related records are represented by their codes."""

from __future__ import annotations

from typing import TYPE_CHECKING

from rest_framework import serializers

from naija_geo.django.models import LGA, State, Zone

# DRF's serializers are only generic in djangorestframework-stubs, not at runtime.
if TYPE_CHECKING:
    _ZoneSerializer = serializers.ModelSerializer[Zone]
    _StateSerializer = serializers.ModelSerializer[State]
    _LGASerializer = serializers.ModelSerializer[LGA]
else:
    _ZoneSerializer = _StateSerializer = _LGASerializer = serializers.ModelSerializer


class ZoneSerializer(_ZoneSerializer):
    class Meta:
        model = Zone
        fields = ["code", "name"]
        read_only_fields = fields


class StateSerializer(_StateSerializer):
    zone: serializers.SlugRelatedField[Zone] = serializers.SlugRelatedField(
        slug_field="code", read_only=True
    )

    class Meta:
        model = State
        fields = ["code", "name", "slug", "capital", "zone", "aliases"]
        read_only_fields = fields


class LGASerializer(_LGASerializer):
    state: serializers.SlugRelatedField[State] = serializers.SlugRelatedField(
        slug_field="code", read_only=True
    )

    class Meta:
        model = LGA
        fields = ["code", "name", "slug", "state", "aliases"]
        read_only_fields = fields
