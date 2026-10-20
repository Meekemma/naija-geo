from importlib.util import find_spec

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
]
if find_spec("rest_framework") is not None:
    urlpatterns.append(path("api/locations/", include("naija_geo.drf.urls")))
