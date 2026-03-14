from django.urls import path
from . import views

urlpatterns = [
    path('', views.property_list_create, name='property-list-create'),
    path('<int:pk>/delete/', views.property_delete, name='property-delete'),
    path('<int:pk>/price/', views.property_update_price, name='property-update-price'),
    path('<int:pk>/update/', views.property_update, name='property-update'),
]
