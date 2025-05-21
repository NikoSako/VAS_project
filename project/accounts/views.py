from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required

def login_view(request):
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            messages.error(request, "Няма акаунт с този имейл")
            return redirect('login')

        user = authenticate(request, username=user.username, password = password)
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, "Грешен имейл или парола")
            return redirect('login')
        
    return render(request, 'login.html')

def signup_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        password2 = request.POST['password2']

        if password != password2:
            messages.error(request, "Паролите не съвпадат")
            return redirect('signup')
        
        if  User.objects.filter(username = username).exists():
            messages.error(request, "Името вече съществува")
            return redirect('signup')
        
        if User.objects.filter(email = email).exists():
            messages.error(request, "Имейлът вече съществува")
            return redirect('signup')
        
        user = User.objects.create_user(username=username, email=email,  password=password)
        user.save()
        login(request, user)
        return redirect('dashboard')

    return render(request, 'signup.html')

def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
def dashboard_view(request):
    return render(request, 'dashboard.html')