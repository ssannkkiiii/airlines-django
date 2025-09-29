from django.db import models
import google.auth.transport.requests
import google.oauth2.id_token

from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    class UserRoles(models.TextChoices):
        ADMIN = 'admin', 'Admin'
        CLIENT = 'client', 'Client'
        
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=255, verbose_name='User first name')
    last_name = models.CharField(max_length=255, verbose_name='User last name')
    date_of_birth = models.DateField(null=True, blank=True)
    google_id = models.CharField(max_length=100, unique=True, null=True, blank=True)

    role = models.CharField(
        max_length=20,
        choices=UserRoles.choices,
        default=UserRoles.CLIENT,
        verbose_name='User role'
    )
    
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ['username']
    
    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
    
    @property
    def get_full_name(self):
        return f'{self.first_name} {self.last_name}'
    
    def save(self, *args, **kwargs):
        if not self.username:
            self.username = self.email.split('@')[0]
        super().save(*args, **kwargs)
        
    @classmethod
    def from_google_token(cls, token: str) -> "User":
        request = google.auth.transport.requests.Request()
        id_info = google.oauth2.id_token.verify_oauth2_token(token, request)

        google_id = id_info["sub"]
        email = id_info.get("email")
        name = id_info.get("name")
        picture = id_info.get("picture")

        user, created = cls.objects.get_or_create(
            google_id=google_id,
            defaults={"username": email, "email": email, "first_name": name},
        )
        if picture:
            user.avatar = picture
            user.save(update_fields=["avatar"])
        return user