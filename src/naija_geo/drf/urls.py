"""``path("api/locations/", include("naija_geo.drf.urls"))``"""

from rest_framework.routers import DefaultRouter

from naija_geo.drf.views import LGAViewSet, StateViewSet, ZoneViewSet

app_name = "naija_geo"

router = DefaultRouter()
router.register("zones", ZoneViewSet, basename="zone")
router.register("states", StateViewSet, basename="state")
router.register("lgas", LGAViewSet, basename="lga")

urlpatterns = router.urls
