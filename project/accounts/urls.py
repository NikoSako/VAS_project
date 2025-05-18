from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name = 'login'),
    path('', views.signup_view, name = 'signup'),
    path('logout/', views.logout_view, name = 'logout'),
    path('dashboad/', views.dashboard_view, name='dashboard'),
]