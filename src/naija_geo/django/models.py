"""Database copies of the bundled data, filled by ``manage.py load_naija_geo``.

The JSON data is the source of truth; rows are upserted by ``code``, so foreign keys from
your own models survive reloads.
"""

from django.db import models


class Zone(models.Model):
    code = models.CharField(max_length=2, unique=True)
    name = models.CharField(max_length=50)

    class Meta:
        ordering = ["code"]

    def __str__(self) -> str:
        return self.name


class State(models.Model):
    code = models.CharField(max_length=5, unique=True)  # NG-LA
    name = models.CharField(max_length=50)
    slug = models.SlugField(unique=True)
    capital = models.CharField(max_length=50)
    zone = models.ForeignKey(Zone, on_delete=models.PROTECT, related_name="states")
    aliases = models.JSONField(default=list, blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class LGA(models.Model):
    code = models.CharField(max_length=8, unique=True)  # NG-LA-11
    name = models.CharField(max_length=100)
    slug = models.SlugField()
    state = models.ForeignKey(State, on_delete=models.PROTECT, related_name="lgas")
    aliases = models.JSONField(default=list, blank=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "LGA"
        verbose_name_plural = "LGAs"
        constraints = [
            models.UniqueConstraint(fields=["state", "slug"], name="uniq_lga_per_state"),
        ]

    def __str__(self) -> str:
        return self.name
