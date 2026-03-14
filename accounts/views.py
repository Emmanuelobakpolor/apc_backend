from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils import timezone

from .models import User
from .serializers import (
    SendOTPSerializer,
    VerifyOTPSerializer,
    RegisterSerializer,
    AgentSignupSerializer,
    OwnerSignupSerializer,
    LoginSerializer,
    MeSerializer,
    UpdateProfileSerializer,
)
from .utils import send_otp_email, verify_otp


def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    refresh['role'] = user.role
    refresh['full_name'] = user.get_full_name()
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }


# ── OTP endpoints ──────────────────────────────────────────────────────────────

@api_view(['POST'])
@permission_classes([AllowAny])
def send_otp(request):
    serializer = SendOTPSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    email = serializer.validated_data['email']
    try:
        send_otp_email(email)
    except Exception:
        return Response(
            {'detail': 'Failed to send OTP. Please try again.'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
    return Response({'detail': 'OTP sent successfully.'}, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
def verify_otp_view(request):
    """
    Verifies the OTP. On success:
    - Activates the user account (is_active = True)
    - Returns JWT tokens + user data so the user is immediately logged in
    """
    serializer = VerifyOTPSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    email = serializer.validated_data['email'].lower()
    otp_code = serializer.validated_data['otp']

    if not verify_otp(email, otp_code):
        return Response(
            {'detail': 'Invalid or expired OTP.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Activate the account
    try:
        user = User.objects.get(email=email)
        user.is_active = True
        user.save(update_fields=['is_active'])
    except User.DoesNotExist:
        # OTP verified but no user yet (standalone OTP flow) — still return success
        return Response({'verified': True}, status=status.HTTP_200_OK)

    # Issue JWT tokens immediately (no extra login step needed)
    tokens = get_tokens_for_user(user)
    return Response(
        {
            'verified': True,
            'user': MeSerializer(user, context={'request': request}).data,
            **tokens,
        },
        status=status.HTTP_200_OK,
    )


@api_view(['POST'])
@permission_classes([AllowAny])
def resend_otp(request):
    """Re-send OTP for a registered but unverified email."""
    email = request.data.get('email', '').lower().strip()
    if not email:
        return Response({'detail': 'email is required.'}, status=status.HTTP_400_BAD_REQUEST)

    # Don't reveal whether the email exists
    try:
        user = User.objects.get(email=email)
        if user.is_active:
            return Response(
                {'detail': 'This account is already verified.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
    except User.DoesNotExist:
        pass  # Silently continue — don't expose user existence

    try:
        send_otp_email(email)
    except Exception:
        return Response(
            {'detail': 'Failed to send OTP. Please try again.'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
    return Response({'detail': 'New verification code sent.'})


# ── Unified register (Flutter sign-up) ────────────────────────────────────────

@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    """
    Single sign-up endpoint for all account types.
    Creates an inactive user and sends OTP to their email.
    """
    serializer = RegisterSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    user = serializer.save()

    try:
        send_otp_email(user.email)
    except Exception:
        # Still return 201 — user was created. They can resend OTP.
        pass

    return Response(
        {
            'detail': 'Account created. Please check your email for the verification code.',
            'email': user.email,
        },
        status=status.HTTP_201_CREATED,
    )


# ── Legacy role-specific signup endpoints ─────────────────────────────────────

@api_view(['POST'])
@permission_classes([AllowAny])
def agent_signup(request):
    serializer = AgentSignupSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    user = serializer.save()
    tokens = get_tokens_for_user(user)
    return Response(
        {
            'detail': 'Agent account created successfully.',
            'user': MeSerializer(user, context={'request': request}).data,
            **tokens,
        },
        status=status.HTTP_201_CREATED,
    )


@api_view(['POST'])
@permission_classes([AllowAny])
def owner_signup(request):
    serializer = OwnerSignupSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    user = serializer.save()
    tokens = get_tokens_for_user(user)
    return Response(
        {
            'detail': 'Owner account created successfully.',
            'user': MeSerializer(user, context={'request': request}).data,
            **tokens,
        },
        status=status.HTTP_201_CREATED,
    )


# ── Login ──────────────────────────────────────────────────────────────────────

@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    serializer = LoginSerializer(data=request.data)
    if not serializer.is_valid():
        errors = serializer.errors

        # Extract the email_not_verified signal from validation errors
        non_field = errors.get('non_field_errors', [])
        if non_field and isinstance(non_field[0], dict) and non_field[0].get('email_not_verified'):
            return Response(
                {
                    'error': 'email_not_verified',
                    'detail': 'Please verify your email before logging in.',
                    'email': non_field[0].get('email', ''),
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        return Response(errors, status=status.HTTP_400_BAD_REQUEST)

    user = serializer.validated_data['user']
    tokens = get_tokens_for_user(user)
    return Response(
        {
            'detail': 'Login successful.',
            'user': MeSerializer(user, context={'request': request}).data,
            **tokens,
        },
        status=status.HTTP_200_OK,
    )


@api_view(['POST'])
@permission_classes([AllowAny])
def token_refresh(request):
    from rest_framework_simplejwt.serializers import TokenRefreshSerializer
    serializer = TokenRefreshSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    return Response(serializer.validated_data, status=status.HTTP_200_OK)


# ── Authenticated profile endpoints ───────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def me(request):
    serializer = MeSerializer(request.user, context={'request': request})
    return Response(serializer.data)


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def update_profile(request):
    serializer = UpdateProfileSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    user = serializer.update(request.user, serializer.validated_data)
    user.refresh_from_db()
    return Response(MeSerializer(user, context={'request': request}).data)


@api_view(['POST'])
@permission_classes([AllowAny])
def forgot_password(request):
    """Send an OTP to the email for password reset."""
    email = request.data.get('email', '').lower().strip()
    if not email:
        return Response({'detail': 'email is required.'}, status=status.HTTP_400_BAD_REQUEST)

    # Always send 200 — don't reveal whether email exists
    if User.objects.filter(email=email).exists():
        try:
            send_otp_email(email)
        except Exception:
            return Response(
                {'detail': 'Failed to send OTP. Please try again.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
    return Response({'detail': 'If that email is registered, a reset code has been sent.'})


@api_view(['POST'])
@permission_classes([AllowAny])
def reset_password(request):
    """Verify OTP and set a new password."""
    email = request.data.get('email', '').lower().strip()
    otp_code = request.data.get('otp', '').strip()
    new_password = request.data.get('new_password', '')
    confirm_password = request.data.get('confirm_password', '')

    if not all([email, otp_code, new_password, confirm_password]):
        return Response(
            {'detail': 'email, otp, new_password, and confirm_password are required.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if new_password != confirm_password:
        return Response(
            {'detail': 'Passwords do not match.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if len(new_password) < 8:
        return Response(
            {'detail': 'Password must be at least 8 characters.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if not verify_otp(email, otp_code):
        return Response(
            {'detail': 'Invalid or expired OTP.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        return Response({'detail': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)

    user.set_password(new_password)
    user.is_active = True  # activate in case they were unverified
    user.save(update_fields=['password', 'is_active'])

    return Response({'detail': 'Password reset successfully. You can now log in.'})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password(request):
    old_password = request.data.get('old_password')
    new_password = request.data.get('new_password')

    if not old_password or not new_password:
        return Response(
            {'detail': 'old_password and new_password are required.'},
            status=status.HTTP_400_BAD_REQUEST,
        )
    if not request.user.check_password(old_password):
        return Response(
            {'detail': 'Current password is incorrect.'},
            status=status.HTTP_400_BAD_REQUEST,
        )
    if len(new_password) < 8:
        return Response(
            {'detail': 'New password must be at least 8 characters.'},
            status=status.HTTP_400_BAD_REQUEST,
        )
    request.user.set_password(new_password)
    request.user.save()
    return Response({'detail': 'Password changed successfully.'})
