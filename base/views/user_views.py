from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from base.models import Profile
from django.contrib import messages

from base.forms import UserForm  # or wherever your form is

def login_user(request):
    page = "login"

    if request.user.is_authenticated:
        return redirect("home")

    if request.method == "POST":
        username = request.POST.get("username").lower()
        password = request.POST.get("password")
        
        try:
            user = User.objects.get(username=username)
        except:
            messages.error(request, "User does not exist")
            return redirect("home")
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect("home")
        else:
            messages.error(request, "Password is incorrect")
            return redirect("home")

    context = {"page": page}
    return render(request, "base/main/login.html", context)


def register_user(request):
    form = UserForm()

    if request.method == "POST":
        form = UserForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("home")
        else:
            messages.error(request, "An error occurred during registration")

    context = {"page": "register", "form": form}
    return render(request, "base/main/register.html", context)



def logout_user(request):
    logout(request)
    return redirect("login")