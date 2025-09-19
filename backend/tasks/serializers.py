from django.db import transaction
from django.utils import timezone
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from .models import Country, Airport, Airline, Airplane, Flight, Ticket
from users.models import User

class CountrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Country
        fields = ('id', 'slug', 'name')
        read_only_fields = ('id', 'slug')
        
class AirportReadSerializer(serializers.ModelSerializer):
    country = CountrySerializer(read_only=True)

    class Meta:
        model = Airport
        fields = ('id', 'slug', 'name', 'city', 'country')
        read_only_fields = ('id', 'slug')
        
class AirportWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Airport
        fields = ('id', 'slug', 'name', 'city', 'country')
        read_only_fields = ('id', 'slug')

class AirlineReadSerializer(serializers.ModelSerializer):
    airport = AirportReadSerializer(read_only=True)

    class Meta:
        model = Airline
        fields = ('id', 'slug', 'name', 'airport')
        read_only_fields = ('id', 'slug')
        
class AirlineWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Airline
        fields = ('id', 'slug', 'name', 'airport')
        read_only_fields = ('id', 'slug')
        
class AirplaneReadSerializer(serializers.ModelSerializer):
    airline = AirlineReadSerializer(read_only=True)

    class Meta:
        model = Airplane
        fields = ('id', 'slug', 'model', 'capacity', 'airline')
        read_only_fields = ('id', 'slug')
        
class AirplaneWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Airplane
        fields = ('id', 'slug', 'model', 'capacity', 'airline')
        read_only_fields = ('id', 'slug')
        
class FlightReadSerializer(serializers.ModelSerializer):
    airplane = AirplaneReadSerializer(read_only=True)
    departure_airport = AirportReadSerializer(read_only=True)
    arrival_airport = AirportReadSerializer(read_only=True)
    duration = serializers.SerializerMethodField()
    available_seats = serializers.SerializerMethodField()
    
    class Meta:
        model = Flight
        fields = (
            'id', 'flight_number', 'airplane',
            'departure_airport', 'arrival_airport',
            'departure_time', 'arrival_time', 'status',
            'duration', 'available_seats'
        )
        read_only_fields = ('id', 'duration', 'available_seats')
        
    def get_duration(self, obj):
        if obj.arrival_time and obj.departure_time:
            delta = obj.arrival_time - obj.departure_time
            return int(delta.total_cecond() // 60)
        return None 
    
    def get_avaivble_seats(self, obj):
        occupied = obj.tickets.exclude(status=Ticket.TicketStatus.FAILED).count()
        return max(obj.airplane.capacity - occupied, 0)
    
    