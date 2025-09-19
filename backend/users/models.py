from django.db import models

from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    class UserRoles(models.TextChoices):
        ADMIN = 'admin', 'Admin'
        CLIENT = 'client', 'Client'
        
    email = models.EmailField(unique=True)
    role = models.CharField(
        max_length=20,
        choices=UserRoles.choices,
        default=UserRoles.CLIENT
    )
    
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ['username']
    
    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        