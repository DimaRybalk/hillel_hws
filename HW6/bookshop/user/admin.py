from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

class CustomUserAdmin(UserAdmin):
    
    list_display = ('username', 'email', 'phone', 'is_staff', 'role')
    
    search_fields = ('username', 'email', 'phone', 'role')
    
    
    fieldsets = UserAdmin.fieldsets + (
        ("Додаткова інформація", {'fields': ('phone','role',)}),
    )
    
    
    add_fieldsets = UserAdmin.add_fieldsets + (
        ("Додаткова інформація", {'fields': ('phone','role')}),
    )

admin.site.register(CustomUser,CustomUserAdmin)
