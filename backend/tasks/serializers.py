from rest_framework import serializers
from .models import Country, Airport, Airline, Airplane, Flight, Order, Ticket
from users.serializers import UserProfileSerializer
from django.db import transaction
from .cancel_order import cancel_unpaid_order

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
            "total_seats", "seat_configuration"
        ]
        read_only_fields = ["id", "slug", "total_seats", "seat_configuration"]
        
    def get_seat_configuration(self, obj):
        return obj.get_seat_configuration()
    
    def get_total_seats(self, obj):
        return obj.get_total_seats()


class FlightSerializer(serializers.ModelSerializer):
    airplane = AirplaneSerializer(read_only=True)
    departure_airport = AirportSerializer(read_only=True)
    arrival_airport = AirportSerializer(read_only=True)
    seat_availability = serializers.SerializerMethodField()
    
    airplane_id = serializers.PrimaryKeyRelatedField(
        queryset=Airplane.objects.all(), source="airplane", write_only=True
    )
    departure_airport_id = serializers.PrimaryKeyRelatedField(
        queryset=Airport.objects.all(), source="departure_airport", write_only=True
    )
    arrival_airport_id = serializers.PrimaryKeyRelatedField(
        queryset=Airport.objects.all(), source="arrival_airport", write_only=True
    )

    class Meta:
        model = Flight
        fields = [
            "id", "flight_number", "airplane", "airplane_id", "departure_airport", 
            "departure_airport_id", "arrival_airport", "arrival_airport_id",
            "departure_time", "arrival_time", "status", "economy_seats", "business_seats", 
            "first_class_seats", "seat_availability"
        ]
        read_only_fields = ("id", "economy_seats", "business_seats", "first_class_seats")

    def get_seat_availability(self, obj):
        return {
            'economy': obj.economy_seats,
            'business': obj.business_seats,
            'first_class': obj.first_class_seats
        }
    
    
class TicketSerializer(serializers.ModelSerializer):
    flight = serializers.SerializerMethodField()
    
    class Meta:
        model = Ticket
        fields = ["id", "seat_number", "seat_class", "direction", "price", "flight"]
        read_only_fields = ("id", "flight")
    
    def get_flight(self, obj):
        flight = obj.flight
        if flight:
            return {
                "id": flight.id,
                "flight_number": flight.flight_number,
                "departure_airport": flight.departure_airport.city,
                "arrival_airport": flight.arrival_airport.city,
                "departure_time": flight.departure_time,
                "arrival_time": flight.arrival_time,
                "status": flight.status
            }
        return None


class OrderSerializer(serializers.ModelSerializer):
    user = UserProfileSerializer(read_only=True)
    flight = FlightSerializer(read_only=True)
    return_flight = FlightSerializer(read_only=True)
    tickets = TicketSerializer(many=True, read_only=True)
    is_one_way = serializers.ReadOnlyField()
    is_round_trip = serializers.ReadOnlyField()
    
    flight_id = serializers.PrimaryKeyRelatedField(
        queryset=Flight.objects.all(), source="flight", write_only=True
    )
    return_flight_id = serializers.PrimaryKeyRelatedField(
        queryset=Flight.objects.all(), source="return_flight", write_only=True, required=False
    )

    class Meta:
        model = Order
        fields = [
            "id", "user", "flight", "flight_id", "return_flight", "return_flight_id",
            "ticket_type", "status", "total_price", "created_at", "tickets", "tickets_data",
            "is_one_way", "is_round_trip"
        ]
        read_only_fields = ("id", "user", "total_price", "created_at", "tickets", "is_one_way", "is_round_trip")

    def create(self, validated_data):
        user = self.context['request'].user
        flight = validated_data['flight']
        return_flight = validated_data.get('return_flight')
        ticket_type = validated_data.get('ticket_type', Order.TicketType.ONE_WAY)
        tickets_data = self.context['request'].data.get('tickets', [])
        
        if not tickets_data:
            raise serializers.ValidationError("At least one ticket is required.")
        
        total_price = 0
        
        for ticket_data in tickets_data:
            direction = ticket_data.get('direction', 'outbound')
            target_flight = return_flight if direction == 'return' else flight
            
            if not target_flight:
                raise serializers.ValidationError(f"No flight available for {direction} direction.")
            
            available_seats = target_flight.get_available_seats(ticket_data['seat_class'])
            if available_seats <= 0:
                flight_name = "return flight" if direction == 'return' else "outbound flight"
                raise serializers.ValidationError(f"{flight_name}: No {ticket_data['seat_class']} seats available.")
            
            total_price += ticket_data['price']
        
        order = Order.objects.create(
            user=user, flight=flight, return_flight=return_flight,
            ticket_type=ticket_type, status=Order.OrderStatus.BOOKED,
            total_price=total_price, tickets_data=tickets_data
        )
        
        cancel_unpaid_order.apply_async((order.id,), countdown=60)
        return order