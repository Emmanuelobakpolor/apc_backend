from django.contrib import admin
from .models import Property


@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = ('title', 'agent', 'property_type', 'listing_type', 'price', 'status', 'created_at')
    list_filter = ('property_type', 'listing_type', 'status')
    search_fields = ('title', 'address', 'city_state', 'agent__email')
    ordering = ('-created_at',)
