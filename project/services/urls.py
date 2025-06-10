from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('order/', views.create_order, name='create_order'),
    path('preview-order/', views.preview_order, name='preview_order'),
    path('confirm-order/', views.confirm_order, name='confirm_order'),
    path('details/<int:order_id>/', views.service_details, name='service_details'),

    path('api/orders/', views.order_api, name='order_api'),
    path('api/orders/<int:order_id>/', views.order_api, name='order_api_detail'),
]