"""View-only admin. The data comes from the bundled JSON via ``load_naija_geo``, which would
overwrite any edit made here, so adding, changing and deleting are disabled."""

from typing import TYPE_CHECKING, Any

from django.contrib import admin
from django.http import HttpRequest

from naija_geo.django.models import LGA, State, Zone

# Django's admin classes are only generic in django-stubs, not at runtime.
if TYPE_CHECKING:
    _ZoneAdmin = admin.ModelAdmin[Zone]
    _StateAdmin = admin.ModelAdmin[State]
    _LGAAdmin = admin.ModelAdmin[LGA]
    _StateInline = admin.TabularInline[State, Zone]
    _LGAInline = admin.TabularInline[LGA, State]
else:
    _ZoneAdmin = _StateAdmin = _LGAAdmin = admin.ModelAdmin
    _StateInline = _LGAInline = admin.TabularInline


class ReadOnlyMixin:
    def has_add_permission(self, request: HttpRequest, obj: Any = None) -> bool:
        return False

    def has_change_permission(self, request: HttpRequest, obj: Any = None) -> bool:
        return False

    def has_delete_permission(self, request: HttpRequest, obj: Any = None) -> bool:
        return False


class StateInline(ReadOnlyMixin, _StateInline):
    model = State
    fields = ["code", "name", "capital"]
    show_change_link = True
    extra = 0


class LGAInline(ReadOnlyMixin, _LGAInline):
    model = LGA
    fields = ["code", "name", "aliases"]
    show_change_link = True
    extra = 0


@admin.register(Zone)
class ZoneAdmin(ReadOnlyMixin, _ZoneAdmin):
    list_display = ["code", "name"]
    search_fields = ["code", "name"]
    inlines = [StateInline]


@admin.register(State)
class StateAdmin(ReadOnlyMixin, _StateAdmin):
    list_display = ["name", "code", "capital", "zone"]
    list_filter = ["zone"]
    list_select_related = ["zone"]
    search_fields = ["name", "code", "aliases"]
    inlines = [LGAInline]


@admin.register(LGA)
class LGAAdmin(ReadOnlyMixin, _LGAAdmin):
    list_display = ["name", "code", "state"]
    list_filter = ["state__zone", "state"]
    list_select_related = ["state"]
    search_fields = ["name", "code", "aliases"]
