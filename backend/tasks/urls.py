from rest_framework.routers import DefaultRouter
from django.urls import path, include
from .views import CountryViewSet, AirportViewSet, AirlineViewSet, AirplaneViewSet

router = DefaultRouter()
router.register(r"countries", CountryViewSet, basename="country")
router.register(r"airports", AirportViewSet, basename="airport")
router.register(r"airlines", AirlineViewSet, basename="airline")
router.register(r"airplanes", AirplaneViewSet, basename="airplane")

urlpatterns = [
    path("api/", include(router.urls)),
]
