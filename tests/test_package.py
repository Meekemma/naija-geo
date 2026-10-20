from importlib.metadata import version

import naija_geo


def test_version_matches_package_metadata() -> None:
    # The release workflow checks the tag against pyproject.toml; this keeps __version__ in step.
    assert naija_geo.__version__ == version("naija-geo")
