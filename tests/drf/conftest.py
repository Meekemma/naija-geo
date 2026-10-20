from io import StringIO

import pytest
from django.core.management import call_command


@pytest.fixture
def loaded(db: None) -> None:
    """A database with the bundled data loaded."""
    call_command("load_naija_geo", stdout=StringIO())
