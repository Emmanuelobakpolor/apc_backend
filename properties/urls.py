from django.urls import path
from . import views

urlpatterns = [
    path('listings/', views.property_listings, name='property-listings'),
    path('inquiries/', views.my_inquiries, name='my-inquiries'),
    path('inquiries/<int:pk>/read/', views.mark_inquiry_read, name='mark-inquiry-read'),
    path('inquiries/<int:pk>/delete/', views.delete_inquiry, name='delete-inquiry'),
    path('inquiries/<int:pk>/replies/', views.inquiry_replies, name='inquiry-replies'),
    path('inquiries/<int:pk>/replies/<int:reply_id>/', views.delete_inquiry_reply, name='delete-inquiry-reply'),
    path('', views.property_list_create, name='property-list-create'),
    path('<int:pk>/delete/', views.property_delete, name='property-delete'),
    path('<int:pk>/price/', views.property_update_price, name='property-update-price'),
    path('<int:pk>/update/', views.property_update, name='property-update'),
    path('<int:pk>/inquire/', views.send_inquiry, name='send-inquiry'),
]
