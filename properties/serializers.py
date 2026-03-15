from rest_framework import serializers
from .models import Property, Inquiry, InquiryReply


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
            'price', 'description', 'status', 'front_image', 'side_image', 'back_image',
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


class InquiryReplySerializer(serializers.ModelSerializer):
    sender_name = serializers.SerializerMethodField()
    sender_id = serializers.SerializerMethodField()

    class Meta:
        model = InquiryReply
        fields = ['id', 'message', 'sender_name', 'sender_id', 'is_read', 'created_at']
        read_only_fields = ['id', 'sender_name', 'sender_id', 'is_read', 'created_at']

    def get_sender_name(self, obj):
        return obj.sender.get_full_name() if obj.sender else ''

    def get_sender_id(self, obj):
        return obj.sender_id


class InquirySerializer(serializers.ModelSerializer):
    property_title = serializers.SerializerMethodField()
    property_location = serializers.SerializerMethodField()
    agent_name = serializers.SerializerMethodField()
    replies = InquiryReplySerializer(many=True, read_only=True)
    unread_reply_count = serializers.SerializerMethodField()

    class Meta:
        model = Inquiry
        fields = [
            'id', 'property', 'property_title', 'property_location', 'agent_name',
            'name', 'phone', 'email', 'role', 'message', 'is_read', 'created_at',
            'replies', 'unread_reply_count',
        ]
        read_only_fields = [
            'id', 'property', 'property_title', 'property_location', 'agent_name',
            'is_read', 'created_at', 'replies', 'unread_reply_count',
        ]

    def get_property_title(self, obj):
        return obj.property.title

    def get_property_location(self, obj):
        return obj.property.city_state or obj.property.address

    def get_agent_name(self, obj):
        return obj.property.agent.get_full_name()

    def get_unread_reply_count(self, obj):
        # Count replies not sent by the inquiry sender that are unread
        return obj.replies.exclude(sender=obj.sender).filter(is_read=False).count()
