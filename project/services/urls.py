from django.urls import path
from . import views

urlpatterns = [
    path('order/', views.create_order, name='create_order'),
    path('order/<int:order_id>/', views.service_details, name='service_details'),
]