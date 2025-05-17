print("✅ course_management_views loaded")

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Max

from base.decorators import allowed_roles
from base.models import Unit, Topic
from base.forms import UnitForm


# Managing Units
@login_required
@allowed_roles(["teacher"])
def manage_units(request):
    units = Unit.objects.all().order_by("-updated")  # or whatever ordering you want
    return render(request, "base/manage_units.html", {"units": units})

@login_required
@allowed_roles(["teacher"])
def get_unit_form(request):
    form = UnitForm()
    return render(request, "base/partials/unit_form.html", {"form": form})


@login_required
@allowed_roles(["teacher"])
def submit_unit_form_manage(request):
    if request.method == "POST":
        print("IT'S ALIVE!!!!!")
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
    topics = Topic.objects.all().order_by("-updated")
    return render(request, "manage_topics.html", {"topics": topics})


