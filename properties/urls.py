from django.urls import path
from . import views

urlpatterns = [
    path("listings/", views.property_listings, name="property-listings"),

    # Agent / owner — manage inquiries on their properties
    path("inquiries/", views.my_inquiries, name="my-inquiries"),
    path("inquiries/<int:pk>/read/", views.mark_inquiry_read, name="mark-inquiry-read"),
    path("inquiries/<int:pk>/delete/", views.delete_inquiry, name="delete-inquiry"),
    path("inquiries/<int:pk>/replies/", views.inquiry_replies, name="inquiry-replies"),
    path("inquiries/<int:pk>/replies/<int:reply_id>/", views.delete_inquiry_reply, name="delete-inquiry-reply"),

    # User — view and interact with their own sent inquiries (notifications / chat)
    path("my-inquiries/", views.my_sent_inquiries, name="my-sent-inquiries"),
    path("my-inquiries/unread-count/", views.user_unread_count, name="user-unread-count"),
    path("my-inquiries/<int:pk>/reply/", views.user_inquiry_reply, name="user-inquiry-reply"),
    path("my-inquiries/<int:pk>/mark-read/", views.user_mark_inquiry_read, name="user-mark-inquiry-read"),
    path("my-inquiries/<int:pk>/delete/", views.user_delete_inquiry, name="user-delete-inquiry"),
    path("my-inquiries/<int:pk>/replies/<int:reply_id>/delete/", views.user_delete_reply, name="user-delete-reply"),

    path("", views.property_list_create, name="property-list-create"),
    path("<int:pk>/delete/", views.property_delete, name="property-delete"),
    path("<int:pk>/price/", views.property_update_price, name="property-update-price"),
    path("<int:pk>/update/", views.property_update, name="property-update"),
    path("<int:pk>/inquire/", views.send_inquiry, name="send-inquiry"),

    # Admin
    path("admin/all/", views.admin_all_properties, name="admin-all-properties"),
    path("admin/<int:pk>/delete/", views.admin_delete_property, name="admin-delete-property"),
]