from rest_framework import serializers
from .models import Country, Airport, Airline, Airplane, Flight, Ticket

from users.serializers import UserProfileSerializer
from users.models import User

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

    class Meta:
        model = Airplane
        fields = ["id", "slug", "model", "capacity", "airline", "airline_id"]
        read_only_fields = ["id", "slug"]
        

class FlightSerializers(serializers.ModelSerializer):
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
    
    class Meta: 
        model = Flight
        fields = [
            "id",
            "flight_number",
            "airplane", "airplane_id",
            "departure_airport", "departure_airport_id",
            "arrival_airport", "arrival_airport_id",
            "departure_time", "arrival_time", "status",
        ]
        
        read_only_fields = ("id",)

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
    
class TicketSerializer(serializers.ModelSerializer):
    
    user = UserProfileSerializer(read_only=True)
    flight = FlightSerializers(read_only=True)
    
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source="user", write_only=True
    )
    departure_airport_id = serializers.PrimaryKeyRelatedField(
        queryset=Flight.objects.all(), source="flight", write_only=True
    )
    
    class Meta:
        model = Ticket
        fields = ["id", "flight_id", "flight", "user", "seat_number", "price", "status", "created_at"]
    
    def validate_price(self, value):
        if value.price <= 0:
            raise serializers.ValidationError("Price cannot be lower than 0")
        return value 
    
    def validate_seat_number(self, value):
        if len(value) > 5:
            raise serializers.ValidationError("Number to long")
        return value.upper()
    
    def validate(self, data):
        
        flight = data.get('flight')
        seat = data.get('set_number')
        
        if flight and seat:
            
            if Ticket.objects.filter(flight=flight, seat_number__iexact=seat).exists():
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
            if flight.airplane:
                capacity = flight.airplane.capacity

            if capacity is not None and occupied_count >= capacity:
                raise serializers.ValidationError(
                    {"non_field_errors": "Немає вільних місць на цьому рейсі."}
                )
                
        return data 