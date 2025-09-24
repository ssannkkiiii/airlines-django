from rest_framework import serializers
from .models import ( Country, Airport, Airline,
                    Airplane, Flight, Ticket, Seat )

from users.serializers import UserProfileSerializer
from users.models import User
import re


class CountrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Country
        fields = ["id", "slug", "name"]
        read_only_fields = ["id", "slug"]


class AirportSerializer(serializers.ModelSerializer):
    country = CountrySerializer(read_only=True)
    country_id = serializers.PrimaryKeyRelatedField(
        queryset=Country.objects.all(), source="country", write_only=True
    )

    class Meta:
        model = Airport
        fields = ["id", "slug", "name", "city", "country", "country_id"]
        read_only_fields = ["id", "slug"]


class AirlineSerializer(serializers.ModelSerializer):
    airport = AirportSerializer(read_only=True)
    airport_id = serializers.PrimaryKeyRelatedField(
        queryset=Airport.objects.all(), source="airport", write_only=True
    )

    class Meta:
        model = Airline
        fields = ["id", "slug", "name", "airport", "airport_id"]
        read_only_fields = ["id", "slug"]


class AirplaneSerializer(serializers.ModelSerializer):
    airline = AirlineSerializer(read_only=True)
    airline_id = serializers.PrimaryKeyRelatedField(
        queryset=Airline.objects.all(), source="airline", write_only=True
    )
    total_seats = serializers.ReadOnlyField()
    seat_configuration = serializers.ReadOnlyField()

    class Meta:
        model = Airplane
        fields = [
            "id", "slug", "model", "capacity", "airline", "airline_id",
            "economy_seats", "business_seats", "first_class_seats",
            "rows_economy", "seats_per_row_economy",
            "rows_business", "seats_per_row_business", 
            "rows_first_class", "seats_per_row_first_class",
            "total_seats", "seat_configuration"
        ]
        read_only_fields = ["id", "slug", "total_seats", "seat_configuration"]
        
    def get_seat_configuration(self, obj):
        return obj.get_seat_configuration()


class FlightSerializer(serializers.ModelSerializer):
    airplane = AirplaneSerializer(read_only=True)
    departure_airport = AirportSerializer(read_only=True)
    arrival_airport = AirportSerializer(read_only=True)

    airplane_id = serializers.PrimaryKeyRelatedField(
        queryset=Airplane.objects.all(), source="airplane", write_only=True
    )
    departure_airport_id = serializers.PrimaryKeyRelatedField(
        queryset=Airport.objects.all(), source="departure_airport", write_only=True
    )
    arrival_airport_id = serializers.PrimaryKeyRelatedField(
        queryset=Airport.objects.all(), source="arrival_airport", write_only=True
    )
    seat_availability = serializers.SerializerMethodField()


    class Meta:
        model = Flight
        fields = [
            "id",
            "flight_number",
            "airplane", "airplane_id",
            "departure_airport", "departure_airport_id",
            "arrival_airport", "arrival_airport_id",
            "departure_time", "arrival_time", "status",
            "seat_availability"
        ]
        read_only_fields = ("id",)

    def get_seat_availability(self, obj):
        summary = obj.get_seat_availability_summary()
        
        return [
            {
                'seat_class': seat_class,
                'available': data['available'],
                'total': data['total'],
                'occupied': data['occupied'],
                'percentage_available': round((data['available'] / data['total']) * 100, 2) if data['total'] > 0 else 0
            }
            for seat_class, data in summary.items()
        ]
    
    def validate(self, data):
        departure_time = data.get("departure_time")
        arrival_time = data.get("arrival_time")
        departure_airport = data.get("departure_airport")
        arrival_airport = data.get("arrival_airport")

        if departure_time and arrival_time:
            if arrival_time <= departure_time:
                raise serializers.ValidationError(
                    {"arrival_time": "Arrival time must be later than departure time."}
                )

        if departure_airport and arrival_airport:
            if departure_airport == arrival_airport:
                raise serializers.ValidationError(
                    {"arrival_airport": "The arrival airport must be different from the departure airport."}
                )

        return data
    
    
class SeatSerializer(serializers.ModelSerializer):
    airplane = AirplaneSerializer(read_only=True)
    airplane_id = serializers.PrimaryKeyRelatedField(
        queryset=Airplane.objects.all(), source="airplane", write_only=True
    )
    price_multiplier = serializers.ReadOnlyField()
    is_available_for_flight = serializers.SerializerMethodField()

    class Meta:
        model = Seat
        fields = [
            "id", "airplane", "airplane_id", "seat_number", "seat_class",
            "row_number", "seat_letter", "status", "is_window_seat",
            "is_aisle_seat", "is_emergency_exit", "extra_legroom",
            "price_multiplier", "is_available_for_flight", "created_at", "updated_at"
        ]
        read_only_fields = ["id", "airplane", "price_multiplier", "created_at", "updated_at"]
        
    def get_is_available_for_flight(self, obj):
        flight_id = self.context.get('flight_id')
        if flight_id:
            try:
                flight = Flight.objects.get(id=flight_id)
                return obj.is_available(flight)
            except Flight.DoesNotExist:
                return False
        return obj.status == Seat.SeatStatus.AVAILABLE

    def validate_seat_number(self, value):
        if not value:
            return value
        
        pattern = r'^\d+[A-Z]$'
        if not re.match(pattern, value.upper()):
            raise serializers.ValidationError(
                "Seat number must be in format like '1A', '12C', etc."
            )
        return value.upper()
 

class TicketSerializer(serializers.ModelSerializer):
    user = UserProfileSerializer(read_only=True)
    flight = FlightSerializer(read_only=True)
    return_flight = FlightSerializer(read_only=True)

    user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source='user', write_only=True
    )
    flight_id = serializers.PrimaryKeyRelatedField(
        queryset=Flight.objects.all(), source='flight', write_only=True
    )
    return_flight_id = serializers.PrimaryKeyRelatedField(
        queryset=Flight.objects.all(), source='return_flight', write_only=True, required=False
    )

    total_price = serializers.ReadOnlyField()
    is_one_way = serializers.ReadOnlyField()
    is_round_trip = serializers.ReadOnlyField()
    is_multi_city = serializers.ReadOnlyField()

    class Meta:
        model = Ticket
        fields = [
            "id",
            "flight_id", "flight",
            "user", "user_id",
            "seat_id", "seat", "seat_number", "price", "total_price", "status", "ticket_type",
            "return_flight_id", "return_flight", "created_at",
            "is_one_way", "is_round_trip", "is_multi_city",
        ]
        read_only_fields = ("id", "flight", "user", "return_flight", "seat", "created_at")

    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("Price must be greater than 0.")
        return value

    def validate_seat_number(self, value):
        if len(value) > 5:
            raise serializers.ValidationError("Seat number is too long.")
        return value.upper()

    def validate(self, data):
        flight = data.get('flight')  
        seat = data.get('seat')
        seat_number = data.get('seat_number')
        ticket_type = data.get('ticket_type')
        return_flight = data.get('return_flight')

        if ticket_type == Ticket.TicketType.ROUND_TRIP and not return_flight:
            raise serializers.ValidationError(
                {"return_flight": "Return flight is required for round trip tickets."}
            )
        
        if ticket_type == Ticket.TicketType.ONE_WAY and return_flight:
            raise serializers.ValidationError(
                {"return_flight": "Return flight should not be specified for one way tickets."}
            )
        
        if return_flight and flight:
            if return_flight == flight:
                raise serializers.ValidationError(
                    {"return_flight": "Return flight must be different from outbound flight."}
                )
            
            if return_flight.departure_time <= flight.arrival_time:
                raise serializers.ValidationError(
                    {"return_flight": "Return flight departure must be after outbound flight arrival."}
                )

        if flight and (seat or seat_number):
            if seat and seat.airplane != flight.airplane:
                raise serializers.ValidationError(
                    {"seat": "The selected seat does not belong to this flight's airplane."}
                )
            
            if seat and not seat.is_available(flight):
                raise serializers.ValidationError(
                    {"seat": "This seat is not available for this flight."}
                )
            
            if seat_number and Ticket.objects.filter(flight=flight, seat_number__iexact=seat_number).exists():
                raise serializers.ValidationError(
                    {"seat_number": "This seat is already taken on this flight."}
                )

            occupied_statuses = [
                Ticket.TicketStatus.BOOKED,
                Ticket.TicketStatus.PAID,
                Ticket.TicketStatus.USED,
            ]
            occupied_count = Ticket.objects.filter(
                flight=flight, status__in=occupied_statuses
            ).count()

            capacity = None
            if getattr(flight, 'airplane', None):
                capacity = flight.airplane.capacity

            if capacity is not None and occupied_count >= capacity:
                raise serializers.ValidationError(
                    {"non_field_errors": "There are no available seats on this flight."}
                )

        return data