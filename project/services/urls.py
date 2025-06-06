from django.urls import path
from . import views

urlpatterns = [
    path('order/', views.create_order, name='create_order'),
    path('order/preview/', views.preview_order, name='preview_order'),
    path('order/confirm/', views.confirm_order, name='confirm_order'),
    path('order/<int:order_id>/', views.service_details, name='service_details'),
]