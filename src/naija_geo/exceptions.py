"""Errors raised by name lookups."""

from collections.abc import Sequence

from naija_geo.types import LGA, State


class AmbiguousMatchError(LookupError):
    """A name lookup matched more than one record."""

    def __init__(self, query: str, candidates: Sequence[State | LGA], hint: str) -> None:
        self.query = query
        self.candidates = tuple(candidates)
        listed = ", ".join(f"{c.name} ({c.code})" for c in self.candidates)
        super().__init__(f"{query!r} matches {len(self.candidates)} records: {listed}. {hint}")


class AmbiguousStateError(AmbiguousMatchError):
    """``find_state()`` matched more than one state."""

    candidates: tuple[State, ...]

    def __init__(self, query: str, candidates: Sequence[State]) -> None:
        super().__init__(query, candidates, "Look the state up by code instead.")


class AmbiguousLGAError(AmbiguousMatchError):
    """``find_lga()`` matched LGAs in more than one state; pass ``state=`` to choose one."""

    candidates: tuple[LGA, ...]

    def __init__(self, query: str, candidates: Sequence[LGA]) -> None:
        super().__init__(query, candidates, "Pass state= to choose one.")
