"""Nigeria's geopolitical zones, states and Local Government Areas."""

from naija_geo.core import (
    find_lga,
    find_lgas,
    find_state,
    get_lga,
    get_lgas,
    get_state,
    get_states,
    get_zone,
    get_zones,
    search_lgas,
)
from naija_geo.exceptions import AmbiguousLGAError, AmbiguousMatchError, AmbiguousStateError
from naija_geo.types import LGA, State, Zone

__version__ = "0.0.1"

__all__ = [
    "LGA",
    "AmbiguousLGAError",
    "AmbiguousMatchError",
    "AmbiguousStateError",
    "State",
    "Zone",
    "find_lga",
    "find_lgas",
    "find_state",
    "get_lga",
    "get_lgas",
    "get_state",
    "get_states",
    "get_zone",
    "get_zones",
    "search_lgas",
]
