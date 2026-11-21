from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'role', 'is_staff')
    list_filter = UserAdmin.list_filter + ('role',)
    fieldsets = UserAdmin.fieldsets + (('Додатково', {'fields': ('role', 'bio', 'avatar')}),)
    add_fieldsets = UserAdmin.add_fieldsets + (('Додатково', {'fields': ('email', 'role')}),)