from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST

from base.decorators import allowed_roles
from base.models import Unit, Topic, Course
from base.forms import UnitForm, TopicForm


# Managing Units
@login_required
@allowed_roles(["teacher"])
def manage_units(request):
    courses = Course.objects.filter(teacher=request.user)
    units = Unit.objects.all().order_by("-updated")
    return render(request, "base/main/manage_units.html", {"units": units,"courses": courses})


@login_required
@allowed_roles(["teacher"])
def get_unit_form(request):
    form = UnitForm()
    return render(request, "base/components/unit_components/unit_form.html", {"form": form})


@login_required
@allowed_roles(["teacher"])
def submit_unit_form_manage(request):
    if request.method == "POST":
        form = UnitForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("manage-units")  # Redirect to manage-units page
        else:
            # Re-render the form with errors in the modal
            return render(request, "base/components/unit_components/unit_form.html", {"form": form})
    else:
        form = UnitForm()
        return render(request, "base/components/unit_components/unit_form.html", {"form": form})


# Managing Topics
@login_required
@allowed_roles(["teacher"])
def manage_topics(request):
    courses = Course.objects.filter(teacher=request.user)
    topics = Topic.objects.all().order_by("-updated")
    return render(request, "base/main/manage_topics.html", {"topics": topics, "courses": courses})

@login_required
@allowed_roles(["teacher"])
def get_topic_form(request):
    form = TopicForm()
    return render(request, "base/components/topic_components/topic_form.html", {"form": form})

@require_POST
@login_required
@allowed_roles(["teacher"])
def submit_topic_form(request):
    form = TopicForm(request.POST)
    if form.is_valid():
        form.save()
        return redirect("manage-topics")
    return render(request, "base/components/topic_components/topic_form.html", {"form": form})
