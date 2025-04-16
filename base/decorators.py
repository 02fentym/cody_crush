from django.http import HttpResponse
from django.shortcuts import redirect

def allowed_roles(allowed=[]):
    def decorator(view_func):
        def wrapper_func(request, *args, **kwargs):
            if request.user.is_authenticated:
                role = request.user.profile.role
                if role in allowed:
                    return view_func(request, *args, **kwargs)
                else:
                    return HttpResponse("You are not authorized to view this page.")
            else:
                return redirect("login")
        return wrapper_func
    return decorator
