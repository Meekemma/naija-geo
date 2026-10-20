"""Load the bundled zones, states and LGAs into the database.

Rows are upserted by ``code`` inside one transaction, so running the command again changes
nothing and foreign keys from your own models keep pointing at the same rows. Rows whose code
is no longer in the data are reported but never deleted, because other rows may depend on them.
"""

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any, TypeVar

from django.core.management.base import BaseCommand, CommandParser
from django.db import transaction

import naija_geo
from naija_geo.django.models import LGA, State, Zone

_Model = TypeVar("_Model", Zone, State, LGA)


@dataclass
class SyncResult:
    created: int = 0
    updated: int = 0
    unchanged: int = 0
    stale: list[str] = field(default_factory=list)


def sync(model: type[_Model], rows: Mapping[str, Mapping[str, Any]]) -> SyncResult:
    """Upsert ``rows`` (code -> field values) into ``model``, keyed on ``code``."""
    existing: dict[str, _Model] = {obj.code: obj for obj in model._default_manager.all()}
    result = SyncResult(stale=sorted(set(existing) - set(rows)))
    to_create: list[_Model] = []
    to_update: list[_Model] = []
    changed_fields: set[str] = set()

    for code, values in rows.items():
        obj = existing.get(code)
        if obj is None:
            to_create.append(model(code=code, **values))
            continue
        diff = [name for name, value in values.items() if getattr(obj, name) != value]
        if not diff:
            result.unchanged += 1
            continue
        for name in diff:
            setattr(obj, name, values[name])
        to_update.append(obj)
        changed_fields.update(diff)

    model._default_manager.bulk_create(to_create)
    if to_update:
        model._default_manager.bulk_update(to_update, sorted(changed_fields))
    result.created = len(to_create)
    result.updated = len(to_update)
    return result


def load() -> dict[str, SyncResult]:
    """Upsert all bundled data. Call inside a transaction."""
    zones = sync(Zone, {zone.code: {"name": zone.name} for zone in naija_geo.get_zones()})
    zone_ids = dict(Zone.objects.values_list("code", "id"))
    states = sync(
        State,
        {
            state.code: {
                "name": state.name,
                "slug": state.slug,
                "capital": state.capital,
                "zone_id": zone_ids[state.zone_code],
                "aliases": list(state.aliases),
            }
            for state in naija_geo.get_states()
        },
    )
    state_ids = dict(State.objects.values_list("code", "id"))
    lgas = sync(
        LGA,
        {
            lga.code: {
                "name": lga.name,
                "slug": lga.slug,
                "state_id": state_ids[lga.state_code],
                "aliases": list(lga.aliases),
            }
            for lga in naija_geo.get_lgas()
        },
    )
    return {"Zones": zones, "States": states, "LGAs": lgas}


class Command(BaseCommand):
    help = "Load Nigeria's zones, states and LGAs into the database (safe to re-run)."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Report what would change without saving anything.",
        )

    def handle(self, *args: Any, dry_run: bool = False, **options: Any) -> None:
        with transaction.atomic():
            results = load()
            if dry_run:
                transaction.set_rollback(True)

        for label, result in results.items():
            self.stdout.write(
                f"{label}: {result.created} created, {result.updated} updated, "
                f"{result.unchanged} unchanged"
            )
            if result.stale:
                self.stdout.write(
                    self.style.WARNING(
                        f"{label}: {len(result.stale)} row(s) no longer in the data were left "
                        f"in place: {', '.join(result.stale)}"
                    )
                )
        if dry_run:
            self.stdout.write(self.style.NOTICE("Dry run: no changes were saved."))
        else:
            self.stdout.write(self.style.SUCCESS("naija-geo data is up to date."))
