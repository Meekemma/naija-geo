from django.apps import AppConfig


class NaijaGeoConfig(AppConfig):
    name = "naija_geo.django"
    # Without an explicit label Django would derive "django" from the module path.
    label = "naija_geo"
    verbose_name = "Nigerian locations"
    default_auto_field = "django.db.models.BigAutoField"
