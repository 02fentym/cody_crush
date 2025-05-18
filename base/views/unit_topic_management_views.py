from django.shortcuts import render
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
    return render(request, "base/manage_units.html", {"units": units,"courses": courses})

@login_required
@allowed_roles(["teacher"])
def get_unit_form(request):
    form = UnitForm()
    return render(request, "base/partials/unit_form.html", {"form": form})


@login_required
@allowed_roles(["teacher"])
def submit_unit_form_manage(request):
    if request.method == "POST":
        form = UnitForm(request.POST)
        if form.is_valid():
            form.save()
            units = Unit.objects.all().order_by("-updated")
            return render(request, "base/manage_units_table.html", {"units": units})
    else:
        form = UnitForm()

    return render(request, "base/partials/unit_form.html", {"form": form})


# Managing Topics
@login_required
@allowed_roles(["teacher"])
def manage_topics(request):
    courses = Course.objects.filter(teacher=request.user)
    topics = Topic.objects.all().order_by("-updated")
    return render(request, "base/manage_topics.html", {"topics": topics, "courses": courses})

@login_required
@allowed_roles(["teacher"])
def get_topic_form(request):
    form = TopicForm()
    return render(request, "base/partials/topic_form.html", {"form": form})


@login_required
@allowed_roles(["teacher"])
def get_topic_form(request):
    form = TopicForm()
    return render(request, "base/partials/topic_form.html", {"form": form})


@require_POST
@login_required
@allowed_roles(["teacher"])
def submit_topic_form(request):
    form = TopicForm(request.POST)
    if form.is_valid():
        form.save()
        topics = Topic.objects.all().order_by("-updated")
        return render(request, "base/manage_topics_table.html", {"topics": topics})
    return render(request, "base/partials/topic_form.html", {"form": form})

