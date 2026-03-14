from django.db import models
from django.conf import settings


class Property(models.Model):
    TYPE_CHOICES = [
        ('apartment', 'Apartment'),
        ('villa', 'Villa'),
        ('duplex', 'Duplex'),
        ('bungalow', 'Bungalow'),
        ('studio', 'Studio'),
        ('land', 'Land'),
    ]
    LISTING_CHOICES = [
        ('sale', 'For Sale'),
        ('rent', 'For Rent'),
        ('shortlet', 'Short-let'),
    ]
    FURNISHING_CHOICES = [
        ('fully', 'Fully Furnished'),
        ('semi', 'Semi-Furnished'),
        ('unfurnished', 'Unfurnished'),
    ]
    STATUS_CHOICES = [
        ('available', 'Available'),
        ('sold', 'Sold'),
    ]

    agent = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='properties',
    )
    title = models.CharField(max_length=255)
    property_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    listing_type = models.CharField(max_length=20, choices=LISTING_CHOICES)
    address = models.CharField(max_length=255)
    city_state = models.CharField(max_length=100)
    bedrooms = models.PositiveIntegerField(default=0)
    bathrooms = models.PositiveIntegerField(default=0)
    size_sqm = models.PositiveIntegerField(null=True, blank=True)
    furnishing = models.CharField(max_length=20, choices=FURNISHING_CHOICES, blank=True)
    price = models.DecimalField(max_digits=15, decimal_places=2)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='available')
    front_image = models.ImageField(upload_to='properties/images/', null=True, blank=True)
    side_image = models.ImageField(upload_to='properties/images/', null=True, blank=True)
    back_image = models.ImageField(upload_to='properties/images/', null=True, blank=True)
    ownership_document = models.FileField(upload_to='properties/docs/', null=True, blank=True)
    views_count = models.PositiveIntegerField(default=0)
    inquiries_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.title} ({self.agent.get_full_name()})'
