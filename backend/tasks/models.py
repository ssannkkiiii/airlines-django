from django.db import models
from django.utils.text import slugify
from users.models import User

class Country(models.Model):
    slug = models.SlugField(unique=True, null=True, blank=True)
    name = models.CharField(max_length=255, verbose_name='Country name')
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
        
    class Meta:
        db_table = 'country'
        verbose_name = 'Country'
        verbose_name_plural = 'Countries'
        

class Airport(models.Model):
    slug = models.SlugField(unique=True, blank=True, null=True)
    name = models.CharField(max_length=255, verbose_name='Airport name')
    city = models.CharField(max_length=255, verbose_name="City name")
    country = models.ForeignKey(Country, on_delete=models.CASCADE, related_name='airports')
    
    def __str__(self):
        return f"Airport {self.name} ({self.city})"
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
        
    class Meta:
        db_table = 'airport'
        verbose_name = 'Airport'
        verbose_name_plural = 'Airports'
        

class Airline(models.Model):
    slug = models.SlugField(unique=True, blank=True, null=True)
    name = models.CharField(max_length=100, verbose_name="Airline name")
    airport = models.ForeignKey(Airport, on_delete=models.CASCADE, related_name="airlines")

    def __str__(self):
        return f"Airline {self.name}"
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
        
    class Meta:
        db_table = 'airline'
        verbose_name = 'Airline'
        verbose_name_plural = 'Airlines'   


class Airplane(models.Model):
    slug = models.SlugField(unique=True, null=True, blank=True)
    model = models.CharField(max_length=100)
    capacity = models.PositiveIntegerField()
    airline = models.ForeignKey(Airline, on_delete=models.CASCADE, related_name="airplanes")

    def __str__(self):
        return f"Airplane {self.model} of {self.airline.name}"
    
    def save(self, *args, **kwargs):
        if not self.slug:  
            self.slug = slugify(self.model)
        super().save(*args, **kwargs)
        
    class Meta:
        db_table = 'airplane'
        verbose_name = 'Airplane'
        verbose_name_plural = 'Airplanes'
        

class Flight(models.Model):
    class FlightStatus(models.TextChoices):
        SCHEDULED = 'scheduled', 'Scheduled'
        BOARDING = 'boarding', 'Boarding'
        DEPARTED = 'departed', 'Departed'
        DELAYED = 'delayed', 'Delayed'
        CANCELLED = 'cancelled', 'Cancelled'
    
    flight_number = models.CharField(max_length=10, unique=True)
    airplane = models.ForeignKey(Airplane, on_delete=models.CASCADE, related_name="flights")
    departure_airport = models.ForeignKey(Airport, on_delete=models.CASCADE, related_name="departures")
    arrival_airport = models.ForeignKey(Airport, on_delete=models.CASCADE, related_name="arrivals")
    departure_time = models.DateTimeField()
    arrival_time = models.DateTimeField()
    status = models.CharField(
        max_length=20, 
        choices=FlightStatus.choices, 
        default=FlightStatus.SCHEDULED,
        verbose_name='Flight status'    
    )

    def __str__(self):
        return f"{self.flight_number}: {self.departure_airport.city} -> {self.arrival_airport.city}"
    
    class Meta:
        db_table = 'flight'
        verbose_name = 'Flight'
        verbose_name_plural = 'Flights'
        

class Ticket(models.Model):
    class TicketStatus(models.TextChoices):
        BOOKED = 'booked', 'Booked'
        PAID = 'paid', 'Paid'
        FAILED = 'failed', 'Failed'
        USED = 'used', 'Used'
    
    class TicketType(models.TextChoices):
        ONE_WAY = 'one_way', 'One Way'
        ROUND_TRIP = 'round_trip', 'Round Trip'
        MULTI_CITY = 'multi_city', 'Multi City'

    flight = models.ForeignKey(Flight, on_delete=models.CASCADE, related_name="tickets")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="tickets")
    seat_number = models.CharField(max_length=5)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(
        max_length=20, 
        choices=TicketStatus.choices, 
        default=TicketStatus.BOOKED
    )
    ticket_type = models.CharField(
        max_length=20,
        choices=TicketType.choices,
        default=TicketType.ONE_WAY,
        verbose_name='Ticket Type'
    )
    return_flight = models.ForeignKey(
        Flight, 
        on_delete=models.CASCADE, 
        related_name="return_tickets",
        null=True, 
        blank=True,
        verbose_name='Return Flight'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        from django.core.exceptions import ValidationError
        
        if self.ticket_type == self.TicketType.ROUND_TRIP and not self.return_flight:
            raise ValidationError({
                'return_flight': 'Return flight is required for round trip tickets.'
            })
        
        if self.ticket_type == self.TicketType.ONE_WAY and self.return_flight:
            raise ValidationError({
                'return_flight': 'Return flight should not be specified for one way tickets.'
            })
        
        if self.return_flight and self.return_flight == self.flight:
            raise ValidationError({
                'return_flight': 'Return flight must be different from outbound flight.'
            })
        
        if self.return_flight and self.return_flight.departure_time <= self.flight.arrival_time:
            raise ValidationError({
                'return_flight': 'Return flight departure must be after outbound flight arrival.'
            })
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
    
    @property
    def is_one_way(self):
        return self.ticket_type == self.TicketType.ONE_WAY
    
    @property
    def is_round_trip(self):
        return self.ticket_type == self.TicketType.ROUND_TRIP
    
    @property
    def is_multi_city(self):
        return self.ticket_type == self.TicketType.MULTI_CITY
    
    @property
    def total_price(self):
        if self.is_round_trip and self.return_flight:
            return self.price * 2
        return self.price

    def __str__(self):
        ticket_type_display = self.get_ticket_type_display()
        return f"Ticket {self.id} - {self.user.email} - {self.flight.flight_number} ({ticket_type_display})"
    
    class Meta:
        db_table = 'ticket'
        verbose_name = 'Ticket'
        verbose_name_plural = 'Tickets'


    