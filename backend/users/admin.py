from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    model = User
    list_display = (
        'id', 'email', 'username', 'first_name', 'last_name',
        'role', 'date_of_birth', 'is_active', 'is_staff'
    )
    list_filter = ('role', 'is_active', 'is_staff', 'is_superuser')
    search_fields = ('email', 'username', 'first_name', 'last_name')
    ordering = ('email',)

    fieldsets = (
        (None, {'fields': ('email', 'username', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'date_of_birth')}),
        (_('Permissions'), {
            'fields': (
                'role',
                'is_active',
                'is_staff',
                'is_superuser',
                'groups',
                'user_permissions',
            )
        }),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'password1', 'password2', 'role'),
        }),
    )
