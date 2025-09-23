from rest_framework import viewsets, permissions, filters, status
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import Country, Airport, Airline, Airplane, Flight, Ticket
from .serializers import (
    CountrySerializer,
    AirportSerializer,
    AirlineSerializer,
    AirplaneSerializer,
    FlightSerializers,
    TicketSerializer
)

from users.permissions import IsOwnerOrAdmin

class CountryViewSet(viewsets.ModelViewSet):
    queryset = Country.objects.all()
    serializer_class = CountrySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend]
    search_fields = ["name"]
    ordering_fields = ["name", "id"]
    lookup_field = "slug"


class AirportViewSet(viewsets.ModelViewSet):
    queryset = Airport.objects.select_related("country").all()
    serializer_class = AirportSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend]
    filterset_fields = ["country", "city"]
    search_fields = ["name", "city"]
    ordering_fields = ["name", "city"]
    lookup_field = "slug"


class AirlineViewSet(viewsets.ModelViewSet):
    queryset = Airline.objects.select_related("airport__country").all()
    serializer_class = AirlineSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend]
    filterset_fields = ["airport"]
    search_fields = ["name"]
    ordering_fields = ["name"]
    lookup_field = "slug"


class AirplaneViewSet(viewsets.ModelViewSet):
    queryset = Airplane.objects.select_related("airline__airport").all()
    serializer_class = AirplaneSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend]
    filterset_fields = ["airline"]
    search_fields = ["model"]
    ordering_fields = ["model", "capacity"]
    lookup_field = "slug"


class FlightViewSet(viewsets.ModelViewSet):
    queryset = Flight.objects.select_related(
        "airplane", "airplane__airline", "departure_airport", "arrival_airport"
    ).all()
    serializer_class = FlightSerializers
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend]
    filterset_fields = ["status", "departure_airport", "arrival_airport", "airplane"]
    search_fields = ["flight_number", "airplane__model", "airplane__airline__name"]
    ordering_fields = ["departure_time", "arrival_time", "flight_number"]
    lookup_field = "flight_number"


class TicketViewSet(viewsets.ModelViewSet):
    queryset = Ticket.objects.select_related("flight", "user").all()
    serializer_class = TicketSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrAdmin]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend]
    filterset_fields = ["flight", "status", "user"]
    search_fields = ["seat_number", "flight__flight_number", "user__email"]
    ordering_fields = ["created_at", "price"]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def update(self, request, *args, **kwargs):
        if "flight" in request.data or "user" in request.data:
            return Response(
                {"detail": "You cannot change a flight or user after creation."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return super().update(request, *args, **kwargs)
    