from importlib.util import find_spec

# The core must work without Django, so the Django and DRF suites are skipped when the
# corresponding extras are not installed.
collect_ignore = []
if find_spec("django") is None:
    collect_ignore += ["django", "drf", "settings.py", "urls.py"]
elif find_spec("rest_framework") is None:
    collect_ignore += ["drf"]
