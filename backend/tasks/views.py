from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import Country, Airport, Airline, Airplane, Flight, Order, Ticket
from .serializers import (
    CountrySerializer, AirportSerializer, AirlineSerializer, AirplaneSerializer,
    FlightSerializer, OrderSerializer, TicketSerializer
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
    serializer_class = FlightSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend]
    filterset_fields = ["status", "departure_airport", "arrival_airport", "airplane"]
    search_fields = ["flight_number", "airplane__model", "airplane__airline__name"]
    ordering_fields = ["departure_time", "arrival_time", "flight_number"]
    lookup_field = "flight_number"


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.select_related("user", "flight", "return_flight").all()
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrAdmin]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend]
    filterset_fields = ["ticket_type", "status", "flight", "return_flight"]
    search_fields = ["flight__flight_number", "return_flight__flight_number"]
    ordering_fields = ["created_at", "total_price"]

    def get_queryset(self):
        if self.request.user.is_staff:
            return Order.objects.select_related("user", "flight", "return_flight").all()
        return Order.objects.filter(user=self.request.user).select_related("user", "flight", "return_flight")

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated, IsOwnerOrAdmin])
    def buy(self, request, pk=None):
        order = self.get_object()
        
        if not (request.user.is_staff or order.user == request.user):
            return Response(
                {"detail": "You don't have permission to perform this action."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            order.buy()
            serializer = self.get_serializer(order)
            return Response({
                "message": "Order successfully confirmed and tickets issued!",
                "order": serializer.data
            }, status=status.HTTP_200_OK)
        except ValueError as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated, IsOwnerOrAdmin])
    def cancel(self, request, pk=None):
        order = self.get_object()
        
        if not (request.user.is_staff or order.user == request.user):
            return Response(
                {"detail": "You don't have permission to perform this action."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            order.cancel()
            serializer = self.get_serializer(order)
            return Response({
                "message": "Order successfully cancelled and seats released!",
                "order": serializer.data
            }, status=status.HTTP_200_OK)
        except ValueError as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class TicketViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ticket.objects.select_related("order", "order__flight", "order__return_flight").all()
    serializer_class = TicketSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrAdmin]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend]
    filterset_fields = ["seat_class", "direction", "order__flight", "order__ticket_type"]
    search_fields = ["seat_number", "order__flight__flight_number"]
    ordering_fields = ["seat_number", "price"]

    def get_queryset(self):
        if self.request.user.is_staff:
            return Ticket.objects.select_related("order", "order__flight", "order__return_flight").all()
        return Ticket.objects.filter(order__user=self.request.user).select_related("order", "order__flight", "order__return_flight")
