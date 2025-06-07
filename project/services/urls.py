from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('order/', views.create_order, name='create_order'),
    path('preview-order/', views.preview_order, name='preview_order'),
    path('confirm-order/', views.confirm_order, name='confirm_order'),
    path('details/<int:order_id>/', views.service_details, name='service_details'),
]