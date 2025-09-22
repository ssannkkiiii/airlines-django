from rest_framework import viewsets, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import Country, Airport, Airline, Airplane
from .serializers import (
    CountrySerializer,
    AirportSerializer,
    AirlineSerializer,
    AirplaneSerializer,
)

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

