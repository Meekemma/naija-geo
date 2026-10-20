# naija-geo

Nigeria's 6 geopolitical zones, 36 states + FCT and 774 Local Government Areas as a
dependency-free Python package, with optional Django and Django REST Framework layers.

> **Status:** pre-alpha. The API is complete but not yet released as 1.0.

```bash
pip install naija-geo            # core only, no dependencies
pip install naija-geo[django]    # + Django app
pip install naija-geo[drf]       # + Django app + REST API
```

## Quickstart

```python
from naija_geo import get_states, get_state, find_state, get_lgas, find_lga, search_lgas

get_states(zone="SW")            # [State(code="NG-EK", name="Ekiti", ...), ...]
get_state("NG-LA").capital       # "Ikeja"
find_state("lagos state")        # State(code="NG-LA", ...)

get_lgas("Lagos")                # the 20 LGAs in Lagos (a code or a name works)
find_lga("ifako/ijaye")          # LGA(code="NG-LA-10", name="Ifako-Ijaiye", ...)
search_lgas("ike")               # Ikeduru, Ikeja, Ikenne, Ikere (best match first)
```

Records are frozen dataclasses (`Zone`, `State`, `LGA`). Related records are referenced by
code: `state.zone_code`, `lga.state_code`.

### Lookup rules

- `get_*(code)` looks a record up by code and raises `KeyError` for an unknown code.
- `find_*(name)` looks a record up by name or alias and returns `None` when nothing matches.
  There is no typo guessing, because a wrong guess would silently return the wrong place.
- Names are matched ignoring case, accents, apostrophes and the difference between `-`, `/`
  and spaces. State lookups also ignore "State" and "State of" ("State of Osun").
- Six LGA names exist in more than one state (Bassa, Ifelodun, Irepodun, Nasarawa, Obi and
  Surulere). For these, `find_lga()` raises `AmbiguousLGAError` unless you pass `state=`:

```python
find_lga("surulere")                 # AmbiguousLGAError: ... Pass state= to choose one.
find_lga("surulere", state="Oyo")    # LGA(code="NG-OY-33", ...)
find_lgas("surulere")                # both, never raises
```

## Django

```python
INSTALLED_APPS = [..., "naija_geo.django"]
```

```bash
python manage.py migrate
python manage.py load_naija_geo            # safe to re-run; upserts by code
python manage.py load_naija_geo --dry-run  # report changes without saving
```

This gives you `Zone`, `State` and `LGA` models (`from naija_geo.django.models import LGA`)
to point your own foreign keys at, plus a view-only admin. Re-running `load_naija_geo` after
upgrading the package applies data corrections in place. Row ids never change, and rows are
never deleted.

### Forms with a dependent State → LGA dropdown

```python
from django import forms
from naija_geo.django.fields import (
    LGAChoiceField, StateChoiceField, StateLGAFormMixin, StateLGAWidget,
)

class AddressForm(StateLGAFormMixin, forms.Form):
    state = StateChoiceField()                       # or StateChoiceField(zones=["SW"])
    lga = LGAChoiceField(widget=StateLGAWidget(state_field="state"))
```

Add `{{ form.media }}` to the template. The widget only shows LGAs of the chosen state, using a
small script with no framework and no API calls. `StateLGAFormMixin` also rejects a mismatched
pair on the server. Both fields submit codes (`NG-LA`, `NG-LA-11`).

## Django REST Framework

```python
urlpatterns = [..., path("api/locations/", include("naija_geo.drf.urls"))]
```

| Endpoint | Description |
|---|---|
| `GET /zones/` | All zones |
| `GET /states/?zone=SW` | States, optionally filtered by zone |
| `GET /states/{code}/` | One state |
| `GET /states/{code}/lgas/` | The LGAs in a state (for cascading dropdowns) |
| `GET /lgas/?state=NG-LA&search=ike` | LGAs, optionally filtered by state and searched |
| `GET /lgas/{code}/` | One LGA |

```json
{"code": "NG-LA-11", "name": "Ikeja", "slug": "ikeja", "state": "NG-LA", "aliases": []}
```

Endpoints are read-only and unpaginated, and an unknown `zone` or `state` returns 400. They
use your project's `DEFAULT_PERMISSION_CLASSES`. If that requires login and you need anonymous
access (for example on a sign-up form), subclass the views from `naija_geo.drf.views` with
`permission_classes = [AllowAny]`. The serializers in `naija_geo.drf.serializers` can be
reused in your own views.

## Supported versions

| | Versions |
|---|---|
| Python | 3.11 – 3.15 (core); 3.11 – 3.14 with Django |
| Django | 5.2 LTS, 6.0, 6.1 |
| DRF | 3.16+ |

## Data Sources

- **States, capitals, LGAs:** Constitution of the Federal Republic of Nigeria 1999 (as amended),
  Section 3 and the First Schedule (Parts I & II). LGA names cross-checked in October 2026 against
  INEC's voter registration portal (cvr.inecnigeria.org); INEC's variant spellings are included as aliases.
- **State codes:** ISO 3166-2:NG.
- **Geopolitical zones:** The conventional six-zone grouping used by federal institutions (not constitutionally defined).
- Alternate and historical spellings are recorded in each entry's `aliases`.

Corrections are welcome. Please open an issue with a source.

## Versioning

[Semantic versioning](https://semver.org/). Data corrections are patch releases, new features
are minor releases and breaking changes are major releases. Codes are stable: an LGA's code is
never reused or renumbered. Every data change is recorded in [CHANGELOG.md](CHANGELOG.md)
with its source.

## License

MIT
