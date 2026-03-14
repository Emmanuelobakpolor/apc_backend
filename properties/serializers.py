from rest_framework import serializers
from .models import Property, Inquiry


class PropertySerializer(serializers.ModelSerializer):
    agent_name = serializers.SerializerMethodField()
    agent_phone = serializers.SerializerMethodField()
    front_image_url = serializers.SerializerMethodField()
    side_image_url = serializers.SerializerMethodField()
    back_image_url = serializers.SerializerMethodField()

    class Meta:
        model = Property
        fields = [
            'id', 'title', 'property_type', 'listing_type', 'address',
            'city_state', 'bedrooms', 'bathrooms', 'size_sqm', 'furnishing',
            'price', 'status', 'front_image', 'side_image', 'back_image',
            'front_image_url', 'side_image_url', 'back_image_url',
            'ownership_document', 'views_count', 'inquiries_count',
            'created_at', 'agent_name', 'agent_phone',
        ]
        read_only_fields = [
            'id', 'created_at', 'agent_name', 'agent_phone',
            'views_count', 'inquiries_count',
            'front_image_url', 'side_image_url', 'back_image_url',
        ]

    def get_agent_name(self, obj):
        return obj.agent.get_full_name()

    def get_agent_phone(self, obj):
        # Prefer profile phone_number (AgentProfile / OwnerProfile), fall back to User.phone
        try:
            phone = obj.agent.agent_profile.phone_number
            if phone:
                return phone
        except Exception:
            pass
        try:
            phone = obj.agent.owner_profile.phone_number
            if phone:
                return phone
        except Exception:
            pass
        return obj.agent.phone or ''

    def get_front_image_url(self, obj):
        request = self.context.get('request')
        if obj.front_image and request:
            return request.build_absolute_uri(obj.front_image.url)
        return None

    def get_side_image_url(self, obj):
        request = self.context.get('request')
        if obj.side_image and request:
            return request.build_absolute_uri(obj.side_image.url)
        return None

    def get_back_image_url(self, obj):
        request = self.context.get('request')
        if obj.back_image and request:
            return request.build_absolute_uri(obj.back_image.url)
        return None


class InquirySerializer(serializers.ModelSerializer):
    property_title = serializers.SerializerMethodField()
    property_location = serializers.SerializerMethodField()

    class Meta:
        model = Inquiry
        fields = [
            'id', 'property', 'property_title', 'property_location',
            'name', 'phone', 'email', 'role', 'is_read', 'created_at',
        ]
        read_only_fields = ['id', 'property', 'property_title', 'property_location', 'is_read', 'created_at']

    def get_property_title(self, obj):
        return obj.property.title

    def get_property_location(self, obj):
        return obj.property.city_state or obj.property.address
