from rest_framework import viewsets, permissions, filters, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend
from .models import ( Country, Airport, Airline, 
                     Airplane, Flight, Ticket, Seat, Order )
from .serializers import (
    CountrySerializer,
    AirportSerializer,
    AirlineSerializer,
    AirplaneSerializer,
    FlightSerializer,
    TicketSerializer,
    SeatSerializer,
    OrderSerializer
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


class SeatViewSet(viewsets.ModelViewSet):
    queryset = Seat.objects.select_related("airplane", "airplane__airline").all()
    serializer_class = SeatSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend]
    filterset_fields = ["airplane", "seat_class", "status", "is_window_seat", "is_aisle_seat"]
    search_fields = ["seat_number", "airplane__model"]
    ordering_fields = ["row_number", "seat_letter", "seat_class"]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        flight_id = self.request.query_params.get('flight_id')
        if flight_id:
            context['flight_id'] = flight_id
        return context


class TicketViewSet(viewsets.ModelViewSet):
    queryset = Ticket.objects.select_related("flight", "user", "seat").all()
    serializer_class = TicketSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrAdmin]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend]
    filterset_fields = ["flight", "status", "user", "ticket_type", "seat__seat_class"]
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


class FlightSeatAvailabilityViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Flight.objects.select_related("airplane").all()
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend]
    filterset_fields = ["status", "departure_airport", "arrival_airport", "airplane"]
    search_fields = ["flight_number"]
    ordering_fields = ["departure_time", "arrival_time"]

    def list(self, request, *args, **kwargs):
        flights = self.filter_queryset(self.get_queryset())
        
        availability_data = []
        for flight in flights:
            summary = flight.get_seat_availability_summary()
            flight_data = {
                'flight_id': flight.id,
                'flight_number': flight.flight_number,
                'departure_airport': flight.departure_airport.city,
                'arrival_airport': flight.arrival_airport.city,
                'departure_time': flight.departure_time,
                'arrival_time': flight.arrival_time,
                'status': flight.status,
                'seat_availability': [
                    {
                        'seat_class': seat_class,
                        'available': data['available'],
                        'total': data['total'],
                        'occupied': data['occupied'],
                        'percentage_available': round((data['available'] / data['total']) * 100, 2) if data['total'] > 0 else 0
                    }
                    for seat_class, data in summary.items()
                ]
            }
            availability_data.append(flight_data)
        
        return Response(availability_data)

    def retrieve(self, request, *args, **kwargs):
        flight = self.get_object()
        
        seat_class = request.query_params.get('seat_class')
        available_seats = flight.get_available_seats(seat_class)
        
        seat_serializer = SeatSerializer(
            available_seats, 
            many=True, 
            context={'flight_id': flight.id}
        )
        
        summary = flight.get_seat_availability_summary()
        
        response_data = {
            'flight': {
                'id': flight.id,
                'flight_number': flight.flight_number,
                'departure_airport': flight.departure_airport.city,
                'arrival_airport': flight.arrival_airport.city,
                'departure_time': flight.departure_time,
                'arrival_time': flight.arrival_time,
                'status': flight.status,
            },
            'seat_availability_summary': [
                {
                    'seat_class': seat_class,
                    'available': data['available'],
                    'total': data['total'],
                    'occupied': data['occupied'],
                    'percentage_available': round((data['available'] / data['total']) * 100, 2) if data['total'] > 0 else 0
                }
                for seat_class, data in summary.items()
            ],
            'available_seats': seat_serializer.data
        }
        
        return Response(response_data)


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all().select_related("user", "flight", "seat")
    serializer_class = OrderSerializer
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
        
    @action(detail=True, methods=["post"])
    def pay(self, request, pk=None):
        oreder = self.get_object()
        try:
            ticket = oreder.pay()
            return Response({"message": "Order paid successfully", "ticket_id": ticket.id})
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        order = self.get_object()
        try:
            order.cancel()
            return Response({"message": "Order cancelled"})
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)