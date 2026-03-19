from django.urls import path
from . import views

urlpatterns = [
    # OTP
    path('send-otp/', views.send_otp, name='send-otp'),
    path('verify-otp/', views.verify_otp_view, name='verify-otp'),
    path('resend-otp/', views.resend_otp, name='resend-otp'),

    # Unified register (Flutter sign-up)
    path('register/', views.register, name='register'),

    # Legacy role-specific signup
    path('agent/signup/', views.agent_signup, name='agent-signup'),
    path('owner/signup/', views.owner_signup, name='owner-signup'),

    # Login & token
    path('login/', views.login, name='login'),
    path('token/refresh/', views.token_refresh, name='token-refresh'),

    # Forgot / reset password
    path('forgot-password/', views.forgot_password, name='forgot-password'),
    path('reset-password/', views.reset_password, name='reset-password'),

    # Profile (authenticated)
    path('me/', views.me, name='me'),
    path('me/update/', views.update_profile, name='update-profile'),
    path('me/password/', views.change_password, name='change-password'),

    # One-time setup
    path('create-admin/', views.create_admin, name='create-admin'),

    # Admin
    path('admin/stats/', views.admin_stats, name='admin-stats'),
    path('admin/users/', views.admin_users_list, name='admin-users'),
    path('admin/users/<int:pk>/toggle/', views.admin_toggle_user, name='admin-toggle-user'),
    path('admin/users/<int:pk>/delete/', views.admin_delete_user, name='admin-delete-user'),
]
