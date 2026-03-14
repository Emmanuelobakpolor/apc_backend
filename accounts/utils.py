import random
import string
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from .models import OTPVerification


def generate_otp():
    return ''.join(random.choices(string.digits, k=6))


def send_otp_email(email):
    # Invalidate any previous unused OTPs for this email
    OTPVerification.objects.filter(email=email, is_used=False).update(is_used=True)

    otp = generate_otp()
    expires_at = timezone.now() + timedelta(minutes=settings.OTP_EXPIRY_MINUTES)

    OTPVerification.objects.create(email=email, otp=otp, expires_at=expires_at)

    send_mail(
        subject='Your APC Verification Code',
        message=(
            f'Your verification code is: {otp}\n\n'
            f'This code expires in {settings.OTP_EXPIRY_MINUTES} minutes.\n'
            'Do not share this code with anyone.'
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email],
        fail_silently=False,
    )
    return otp


def verify_otp(email, otp_code):
    try:
        otp_obj = OTPVerification.objects.filter(
            email=email,
            otp=otp_code,
            is_used=False,
        ).latest('created_at')
    except OTPVerification.DoesNotExist:
        return False

    if not otp_obj.is_valid():
        return False

    otp_obj.is_used = True
    otp_obj.save()
    return True
