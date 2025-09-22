from rest_framework import serializers
from .models import Country, Airport, Airline, Airplane


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
        
        
