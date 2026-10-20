"""Immutable records for zones, states and LGAs.

Related entities are referenced by code (``zone_code``, ``state_code``) rather than by
object, so every record is a small, hashable value. Resolve a code with ``get_zone()`` or
``get_state()``.
"""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Zone:
    """A geopolitical zone, e.g. ``Zone(code="SW", name="South West")``."""

    code: str
    name: str

    def __str__(self) -> str:
        return self.name


@dataclass(frozen=True, slots=True)
class State:
    """One of the 36 states or the FCT. ``code`` is the ISO 3166-2:NG code, e.g. ``NG-LA``."""

    code: str
    name: str
    slug: str
    capital: str
    zone_code: str
    aliases: tuple[str, ...] = ()

    def __str__(self) -> str:
        return self.name


@dataclass(frozen=True, slots=True)
class LGA:
    """A Local Government Area (or FCT area council). ``code`` is e.g. ``NG-LA-11``."""

    code: str
    name: str
    slug: str
    state_code: str
    aliases: tuple[str, ...] = ()

    def __str__(self) -> str:
        return self.name
