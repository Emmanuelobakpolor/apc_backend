from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import User, AgentProfile, OwnerProfile, OTPVerification


# ── OTP ────────────────────────────────────────────────────────────────────────

class SendOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()


class VerifyOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6, min_length=6)


# ── Unified Registration (Flutter sign-up form) ────────────────────────────────

class RegisterSerializer(serializers.Serializer):
    """
    Single endpoint for all account types.
    account_type: 'user' | 'agent' | 'property_owner'  (Flutter values)
    """
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    phone = serializers.CharField(max_length=30, required=False, allow_blank=True)
    account_type = serializers.ChoiceField(
        choices=['user', 'agent', 'property_owner'],
        default='user',
        required=False,
    )
    password = serializers.CharField(min_length=8, write_only=True)
    confirm_password = serializers.CharField(min_length=8, write_only=True)

    def validate_email(self, value):
        if User.objects.filter(email=value.lower()).exists():
            raise serializers.ValidationError('An account with this email already exists.')
        return value.lower()

    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError({'confirm_password': 'Passwords do not match.'})
        return data

    def create(self, validated_data):
        validated_data.pop('confirm_password')

        # Map Flutter account_type → backend role
        role_map = {
            'user': 'user',
            'agent': 'agent',
            'property_owner': 'owner',
        }
        account_type = validated_data.pop('account_type')
        role = role_map[account_type]
        first_name = validated_data.pop('first_name')
        last_name = validated_data.pop('last_name')
        phone = validated_data.pop('phone', '')

        user = User.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=first_name,
            last_name=last_name,
            full_name=f'{first_name} {last_name}'.strip(),
            role=role,
            phone=phone,
            is_active=False,   # blocked until OTP verified
        )
        return user


# ── Legacy signup serializers (kept for agent/owner detail signup) ─────────────

class AgentSignupSerializer(serializers.Serializer):
    full_name = serializers.CharField(max_length=255)
    gender = serializers.ChoiceField(choices=['male', 'female', 'other'])
    nationality = serializers.CharField(max_length=100)
    government_id_number = serializers.CharField(max_length=100)
    cac_document = serializers.FileField(required=False, allow_null=True)
    phone_number = serializers.CharField(max_length=20)
    email = serializers.EmailField()
    address = serializers.CharField()
    preferred_contact = serializers.ChoiceField(choices=['email', 'phone', 'whatsapp'])
    password = serializers.CharField(min_length=8, write_only=True)
    confirm_password = serializers.CharField(min_length=8, write_only=True)

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError('An account with this email already exists.')
        return value

    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError({'confirm_password': 'Passwords do not match.'})
        return data

    def create(self, validated_data):
        validated_data.pop('confirm_password')
        cac_document = validated_data.pop('cac_document', None)
        user = User.objects.create_user(
            email=validated_data.pop('email'),
            password=validated_data.pop('password'),
            full_name=validated_data.pop('full_name'),
            role='agent',
            is_active=True,
        )
        AgentProfile.objects.create(
            user=user,
            is_email_verified=True,
            cac_document=cac_document,
            **validated_data,
        )
        return user


class OwnerSignupSerializer(serializers.Serializer):
    full_name = serializers.CharField(max_length=255)
    gender = serializers.ChoiceField(choices=['male', 'female', 'other'])
    nationality = serializers.CharField(max_length=100)
    government_id_number = serializers.CharField(max_length=100)
    id_document = serializers.FileField(required=False, allow_null=True)
    phone_number = serializers.CharField(max_length=20)
    email = serializers.EmailField()
    address = serializers.CharField()
    preferred_contact = serializers.ChoiceField(choices=['email', 'phone', 'whatsapp'])
    password = serializers.CharField(min_length=8, write_only=True)
    confirm_password = serializers.CharField(min_length=8, write_only=True)

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError('An account with this email already exists.')
        return value

    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError({'confirm_password': 'Passwords do not match.'})
        return data

    def create(self, validated_data):
        validated_data.pop('confirm_password')
        id_document = validated_data.pop('id_document', None)
        user = User.objects.create_user(
            email=validated_data.pop('email'),
            password=validated_data.pop('password'),
            full_name=validated_data.pop('full_name'),
            role='owner',
            is_active=True,
        )
        OwnerProfile.objects.create(
            user=user,
            is_email_verified=True,
            id_document=id_document,
            **validated_data,
        )
        return user


# ── Login ──────────────────────────────────────────────────────────────────────

class LoginSerializer(serializers.Serializer):
    """Role is NOT required — any role can log in with email + password."""
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        email = data['email'].lower()
        try:
            user_obj = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError('Invalid email or password.')

        # Check OTP verification before authenticate() (is_active=False blocks authenticate)
        if not user_obj.is_active:
            raise serializers.ValidationError(
                {'email_not_verified': True, 'email': email}
            )

        user = authenticate(email=email, password=data['password'])
        if not user:
            raise serializers.ValidationError('Invalid email or password.')

        data['user'] = user
        return data


# ── Profile read ───────────────────────────────────────────────────────────────

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'full_name', 'role', 'date_joined']


class MeSerializer(serializers.ModelSerializer):
    fullName = serializers.SerializerMethodField()
    accountType = serializers.CharField(source='role', read_only=True)
    phoneNumber = serializers.SerializerMethodField()
    address = serializers.SerializerMethodField()
    avatarUrl = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name', 'full_name', 'fullName',
            'accountType', 'phone', 'phoneNumber', 'location', 'address',
            'avatarUrl', 'date_joined',
        ]

    def _profile(self, obj):
        if obj.role == 'agent':
            return getattr(obj, 'agent_profile', None)
        if obj.role == 'owner':
            return getattr(obj, 'owner_profile', None)
        return None

    def get_fullName(self, obj):
        return obj.get_full_name()

    def get_phoneNumber(self, obj):
        """Phone from the profile model (agent/owner) or directly on user."""
        p = self._profile(obj)
        if p:
            return p.phone_number
        return obj.phone

    def get_address(self, obj):
        p = self._profile(obj)
        if p:
            return p.address
        return obj.location

    def get_avatarUrl(self, obj):
        if obj.profile_picture:
            return obj.profile_picture.url
        return None


# ── Profile update ─────────────────────────────────────────────────────────────

class UpdateProfileSerializer(serializers.Serializer):
    first_name = serializers.CharField(max_length=150, required=False)
    last_name = serializers.CharField(max_length=150, required=False)
    full_name = serializers.CharField(max_length=255, required=False)
    phone = serializers.CharField(max_length=30, required=False, allow_blank=True)
    location = serializers.CharField(max_length=200, required=False, allow_blank=True)
    phone_number = serializers.CharField(max_length=20, required=False, allow_blank=True)
    address = serializers.CharField(required=False, allow_blank=True)
    profile_picture = serializers.ImageField(required=False, allow_null=True)

    def update(self, user, validated_data):
        # Update User fields
        for field in ('first_name', 'last_name', 'phone', 'location'):
            if field in validated_data:
                setattr(user, field, validated_data[field])

        if 'full_name' in validated_data:
            user.full_name = validated_data['full_name']
        elif user.first_name or user.last_name:
            user.full_name = f"{user.first_name} {user.last_name}".strip()

        if 'profile_picture' in validated_data:
            user.profile_picture = validated_data['profile_picture']

        user.save()

        # Update agent/owner profile if exists
        if user.role == 'agent':
            profile = getattr(user, 'agent_profile', None)
        elif user.role == 'owner':
            profile = getattr(user, 'owner_profile', None)
        else:
            profile = None

        if profile:
            if 'phone_number' in validated_data:
                profile.phone_number = validated_data['phone_number']
            if 'address' in validated_data:
                profile.address = validated_data['address']
            profile.save()

        return user
