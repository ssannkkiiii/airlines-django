from rest_framework.routers import DefaultRouter
from django.urls import path, include
from .views import (
    CountryViewSet,
    AirportViewSet,
    AirlineViewSet,
    AirplaneViewSet,
    FlightViewSet,
    TicketViewSet,
    SeatViewSet,
    OrderViewSet
)

router = DefaultRouter()
router.register(r"countries", CountryViewSet, basename="country")
router.register(r"airports", AirportViewSet, basename="airport")
router.register(r"airlines", AirlineViewSet, basename="airline")
router.register(r"airplanes", AirplaneViewSet, basename="airplane")
router.register(r"flights", FlightViewSet, basename="flight")
router.register(r"tickets", TicketViewSet, basename="ticket")
router.register(r'seats', SeatViewSet, basename="seat")
router.register(r"orders", OrderViewSet, basename="order")

urlpatterns = [
    path("", include(router.urls)),
]
