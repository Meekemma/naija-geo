# Nigerian Locations Package: Project Spec (v1)

> **Package name:** `naija-geo` on PyPI (`pip install naija-geo`), imported as `naija_geo` (`from naija_geo import ...`). The name was free on PyPI as of 2026-10-10.
> **Status:** Planning → v1 build
> **Author:** Emmanuel Ibeh (Meeky)

---

## 1. Goal

A reliable, well-tested Python package that provides Nigeria's **geopolitical zones, states (36 + FCT), and all 774 Local Government Areas**, with first-class Django and Django REST Framework support.

The existing Django packages each have a single release, sit in alpha or are stale, and pin only one Django version. This package aims to be the dependable option, with a clean data layer, broad version support, CI and regular releases.

---

## 2. Scope

### In v1
- 6 geopolitical zones
- 37 states (36 + FCT), each with its name, ISO 3166-2 code, capital, zone and slug
- 774 LGAs, each linked to its state and carrying a stable code and spelling aliases
- Pure-Python lookup API with no Django dependency
- An optional Django app with models, a data-loading command, admin and form fields
- An optional DRF layer with serializers, viewsets and cascading endpoints
- Tests that cover both the code and the data itself
- A CI matrix across supported Python and Django versions

### Out of v1 (planned for later)
- Postal codes (v2, once a trustworthy and redistributable data source is confirmed)
- Cities and towns
- Wards
- Lagos LCDAs (to be an optional, clearly separated layer)
- Geo-coordinates and boundaries

**Design rule:** v1 must not block these additions. Every entity gets a stable `code` that future models can reference without breaking changes.

---

## 3. Package Structure

```
naija_geo/
├── pyproject.toml
├── README.md
├── LICENSE                      # MIT
├── CHANGELOG.md
├── src/
│   └── naija_geo/
│       ├── __init__.py          # public API re-exports
│       ├── data/
│       │   ├── zones.json
│       │   ├── states.json
│       │   └── lgas.json
│       ├── core.py              # pure-Python lookups (no Django import)
│       ├── normalize.py         # name normalization + alias matching
│       ├── types.py             # dataclasses: Zone, State, LGA
│       ├── exceptions.py        # AmbiguousMatchError, AmbiguousStateError, AmbiguousLGAError
│       ├── django/              # optional Django layer
│       │   ├── __init__.py
│       │   ├── apps.py
│       │   ├── models.py
│       │   ├── admin.py
│       │   ├── fields.py        # form fields / widgets
│       │   ├── management/commands/load_naija_geo.py
│       │   └── migrations/
│       └── drf/                 # optional DRF layer
│           ├── __init__.py
│           ├── serializers.py
│           ├── views.py
│           └── urls.py
└── tests/
    ├── test_data_integrity.py
    ├── test_core.py
    ├── test_normalize.py
    ├── django/
    └── drf/
```

### Installation extras
```bash
pip install naija-geo            # core only
pip install naija-geo[django]    # + Django layer
pip install naija-geo[drf]       # + Django + DRF layer
```

---

## 4. Data Schema (JSON as source of truth)

The JSON files are the canonical data. The Django models are loaded from them, never the other way round.

### `zones.json`
```json
[
  { "code": "SW", "name": "South West" }
]
```
Zone codes: `NC`, `NE`, `NW`, `SE`, `SS`, `SW`.

### `states.json`
```json
[
  {
    "code": "NG-LA",
    "name": "Lagos",
    "slug": "lagos",
    "capital": "Ikeja",
    "zone": "SW",
    "aliases": ["Lagos State"]
  }
]
```
- `code` uses **ISO 3166-2:NG** (`NG-LA`, `NG-FC` for FCT, and so on), an existing standard that is stable and externally verifiable.

### `lgas.json`
```json
[
  {
    "code": "NG-LA-01",
    "name": "Agege",
    "slug": "agege",
    "state": "NG-LA",
    "aliases": []
  },
  {
    "code": "NG-LA-11",
    "name": "Ifako-Ijaiye",
    "slug": "ifako-ijaiye",
    "state": "NG-LA",
    "aliases": ["Ifako/Ijaiye", "Ifako Ijaye", "Ifako-Ijaye"]
  }
]
```
- `code` format: `<state code>-<2-digit sequence>`, assigned alphabetically within each state at v1 and **frozen afterwards**. New LGAs only ever get appended codes, and existing codes are never reused or renumbered.
- `name` is the canonical spelling and should follow official INEC and government usage.
- `aliases` holds known alternate spellings (slashes, hyphens, older names).

### Data rules
- Exactly 6 zones, 37 states and 774 LGAs.
- Every LGA references a valid state, and every state references a valid zone.
- No duplicate codes or slugs, and no duplicate LGA names within a state.
- Each data source is documented in `README.md` under "Data Sources".

---

## 5. Core API (pure Python)

```python
from naija_geo import (
    get_zones, get_zone,
    get_states, get_state,
    get_lgas, get_lga,
    find_state, find_lga, find_lgas, search_lgas,
    AmbiguousLGAError,
)

get_states()                    # list[State], all 37
get_states(zone="SW")           # states in a zone
get_state("NG-LA")              # by code
find_state("lagos state")       # fuzzy/alias match by name -> State | None

get_lgas("NG-LA")               # LGAs in a state (code or name accepted)
get_lga("NG-LA-11")             # by code
find_lga("ifako/ijaye")         # alias-aware -> LGA | None
find_lga("ikeja", state="NG-LA")
find_lga("surulere")            # raises AmbiguousLGAError (Lagos and Oyo both have one)
find_lga("surulere", state="NG-LA")  # -> LGA
find_lgas("surulere")           # list[LGA], every match, never raises
search_lgas("ike")              # partial match, best first: Ikeduru, Ikeja, Ikenne, Ikere
```

`search_lgas(query, state=None)` is for search boxes and autocomplete. Its results are ranked: exact matches first, then names starting with the query, then names containing it. Ties are ordered by name.

### Ambiguous names
Some LGA names occur in more than one state (Surulere: Lagos and Oyo; Obi: Benue and Nasarawa; and so on).
- `find_lga()` returns the LGA when exactly one matches, and `None` when nothing matches.
- When more than one matches, it raises `AmbiguousLGAError`. The error subclasses `LookupError`, carries the matches in `.candidates`, and its message tells the caller to pass `state=`.
- `find_lgas()` returns every match as a list and never raises. DRF search is built on it.
- `find_state()` follows the same contract for consistency, although no two states currently share a name.

### Behaviour
- Data is loaded once and cached in memory (`functools.lru_cache`).
- `get_*(code)` raises `KeyError` for an unknown code (codes are matched case-insensitively). `find_*(name)` returns `None` when nothing matches. There is no typo guessing, because a wrong guess would silently return the wrong place.
- Wherever a `state` argument is accepted, it may be a state code or a state name.
- `get_states()` and `get_lgas()` return fresh lists in data-file order (states by name, LGAs grouped by state).
- The returned objects are frozen, slotted dataclasses (`Zone`, `State`, `LGA`), and `str()` gives the name. `aliases` is a tuple.
- Related entities are referenced by code: `State.zone_code` and `LGA.state_code`. The different names keep them from being confused with the Django model foreign keys `state.zone` and `lga.state`, which are objects.
- Name matching works through `normalize.py`, which lowercases the input, strips the word "state", treats `-`, `/` and spaces as equivalent, and collapses whitespace.
- No network calls are made, and the core has no third-party dependencies.

---

## 6. Django Layer

### App config
Users add `"naija_geo.django"` to `INSTALLED_APPS`. The `AppConfig` must set `label = "naija_geo"` explicitly. Without it, Django derives the label `"django"` from the module path, which breaks migrations and table names.

### Models
```python
class Zone(models.Model):
    code = models.CharField(max_length=2, unique=True)
    name = models.CharField(max_length=50)

class State(models.Model):
    code = models.CharField(max_length=5, unique=True)   # NG-LA
    name = models.CharField(max_length=50)
    slug = models.SlugField(unique=True)
    capital = models.CharField(max_length=50)
    zone = models.ForeignKey(Zone, on_delete=models.PROTECT, related_name="states")
    aliases = models.JSONField(default=list, blank=True)

class LGA(models.Model):
    code = models.CharField(max_length=8, unique=True)   # NG-LA-11
    name = models.CharField(max_length=100)
    slug = models.SlugField()
    state = models.ForeignKey(State, on_delete=models.PROTECT, related_name="lgas")
    aliases = models.JSONField(default=list, blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["state", "slug"], name="uniq_lga_per_state")]
```

### Loading data
```bash
python manage.py load_naija_geo           # idempotent upsert keyed on `code`
python manage.py load_naija_geo --dry-run
```
- The command must be **idempotent**, so running it twice changes nothing.
- It upserts by `code`, so user foreign keys pointing to these rows survive re-runs.

### Admin
- Search on name, code and aliases, a filter by zone and state, and LGAs shown inline under their state.
- The whole admin is view-only (no add, change or delete). The JSON is the source of truth and `load_naija_geo` would overwrite any edit made in the admin.

### Form fields
- `StateChoiceField`, which can be limited to particular zones.
- `LGAChoiceField`, which is filtered by a chosen state (code, name or `State`).
- Both fields submit codes (`NG-LA`, `NG-LA-11`) rather than database ids.
- An optional `StateLGAWidget` for dependent dropdowns. Every LGA option carries its state code, and a small script with no framework (`static/naija_geo/state_lga.js`) hides the LGAs of other states. Form prefixes are handled.
- `StateLGAFormMixin` rejects an LGA that is not in the chosen state on the server, because the script only filters what the user sees and can be bypassed.

### Load command
- Rows whose code is no longer in the data are reported but never deleted, because user rows may reference them.
- `--dry-run` runs the real upsert inside a transaction and rolls it back, so the counts it reports are exact.

---

## 7. DRF Layer

```python
# urls.py
path("api/locations/", include("naija_geo.drf.urls"))
```

| Endpoint | Description |
|---|---|
| `GET /zones/` | All zones |
| `GET /states/?zone=SW` | States, optionally filtered |
| `GET /states/{code}/` | One state |
| `GET /states/{code}/lgas/` | LGAs in a state (for cascading dropdowns) |
| `GET /lgas/?state=NG-LA` | LGAs, optionally filtered by state (code or name) |
| `GET /lgas/?search=ikeja` | Alias-aware search via `search_lgas()`, best match first (combines with `state`) |
| `GET /lgas/{code}/` | One LGA |

- All endpoints are read-only, and pagination is off because the dataset is small.
- Codes in URLs are matched case-insensitively. Serializers represent related records by code (`"state": "NG-LA"`).
- An unknown `?zone=` or `?state=` returns 400 rather than an empty list.
- Each view sets `filter_backends = []`, so project-wide filter backends cannot reinterpret the query parameters. Permissions follow the project's `DEFAULT_PERMISSION_CLASSES`.
- The serializers are exported so users can reuse them in their own views.

---

## 8. Supported Versions (v1)

| | Versions |
|---|---|
| Python | 3.11 – 3.15 (core); 3.11 – 3.14 with Django |
| Django | 5.2 LTS, 6.0, 6.1 |
| DRF | 3.16+ (first release to support Django 5.2) |

Reviewed 2026-10-10. Django 4.2 reached end of life in April 2026, and Python 3.10 reaches it in October 2026, so neither is supported. Django 6.0 and 6.1 require Python 3.12 or newer. No Django release supports Python 3.15 yet, so 3.15 is tested for the core only until one does.

CI matrix:
- The core alone, with Django not installed, on Python 3.11 – 3.15. This proves the core has no dependencies.
- Django 5.2 on Python 3.11 – 3.14.
- Django 6.0 and 6.1 on Python 3.12 – 3.14.

The matrix should track the Django release schedule, adding new versions and dropping those that reach end of life in a minor release.

---

## 9. Testing

### Data integrity (`test_data_integrity.py`) is the most important suite
- The counts are 6 zones, 37 states and 774 LGAs.
- Per-state LGA counts match the official figures (for example, Lagos has 20 and Kano has 44).
- There are no orphan references and no duplicate codes or slugs.
- All codes match their expected format.
- No alias collides with another LGA's name in the same state.

### Code
- Core lookups and the normalization edge cases.
- An idempotence test for the Django load command.
- Form field validation.
- DRF endpoint responses and filters.

Tooling: `pytest`, `pytest-django`, `tox` or `nox`, `ruff` and `mypy`.

---

## 10. CI / Release

- GitHub Actions should run lint, type checks and the test matrix on every pull request.
- Use semantic versioning: **data corrections are patch releases**, new features are minor releases, and breaking changes are major releases.
- Publish to PyPI through **Trusted Publishing** from a GitHub release.
- Record every data change in `CHANGELOG.md`, giving the source of the correction.

---

## 11. Roadmap

- **v1.0**: Zones, states and LGAs, with the core, Django and DRF layers.
- **v1.x**: Alias coverage improvements and data corrections from issues.
- **v2.0**: Postal codes, subject to a verified and redistributable source. Postcodes map to delivery districts rather than one-to-one to LGAs, so they need their own model (`PostalCode → area → LGA`).
- **Later**: Optional Lagos LCDAs, cities and towns, wards, and coordinates.

---

## 12. v1 Build Checklist

- [x] Package name chosen: `naija-geo`
- [x] Supported versions and the ambiguous-name behaviour decided (2026-10-10)
- [ ] Claim the name on PyPI with a `0.0.1` placeholder release
- [x] Scaffold the repo (`pyproject.toml`, `src/` layout, MIT license)
- [x] Compile `zones.json` and `states.json` (with ISO codes and capitals)
- [x] Compile `lgas.json` (774 entries with aliases)
- [x] Cross-check LGA spellings against official sources (INEC) and document them under "Data Sources"
- [x] Write the data integrity tests and get them passing **before** writing code (LGA checks skip until `lgas.json` exists)
- [x] Core API and normalization
- [x] Django models, migrations and the load command
- [x] Admin and form fields
- [x] DRF serializers, views and URLs
- [x] README with quickstart, examples and data sources
- [x] GitHub Actions CI matrix (`ci.yml`), plus Trusted Publishing release workflow (`release.yml`)
- [ ] Publish 1.0.0 to PyPI
