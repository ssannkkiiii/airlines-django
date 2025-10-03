from rest_framework.routers import DefaultRouter
from django.urls import path, include
from .views import (
    CountryViewSet, AirportViewSet, AirlineViewSet, AirplaneViewSet,
    FlightViewSet, OrderViewSet, TicketViewSet, create_checkout_session, stripe_success, stripe_cancel, stripe_webhook
)

router = DefaultRouter()
router.register(r"countries", CountryViewSet, basename="country")
router.register(r"airports", AirportViewSet, basename="airport")
router.register(r"airlines", AirlineViewSet, basename="airline")
router.register(r"airplanes", AirplaneViewSet, basename="airplane")
router.register(r"flights", FlightViewSet, basename="flight")
router.register(r"orders", OrderViewSet, basename="order")
router.register(r"tickets", TicketViewSet, basename="ticket")

urlpatterns = [
    path("", include(router.urls)),
    
    path("orders/<int:id>/create-checkout-session/", create_checkout_session, name="create-checkout-session"),
    path("stripe/success/", stripe_success),
    path("stripe/cancel/", stripe_cancel),
    path("stripe/webhook/", stripe_webhook),
]