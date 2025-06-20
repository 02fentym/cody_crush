from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib import messages

from base.decorators import allowed_roles
from base.models import Unit, Topic, Course
from base.forms import UnitForm, TopicForm


# Managing Units
@login_required
@allowed_roles(["teacher"])
def manage_units(request):
    courses = Course.objects.filter(teacher=request.user)
    sort_by = request.GET.get("sort_by", "updated")  # Default sort by updated
    order = request.GET.get("order", "desc")  # Default descending

    # Define valid sort fields
    valid_sort_fields = ["title", "description", "updated"]
    if sort_by not in valid_sort_fields:
        sort_by = "updated"

    # Apply sorting
    if order == "asc":
        units = Unit.objects.all().order_by(sort_by)
    else:
        units = Unit.objects.all().order_by(f"-{sort_by}")

    return render(request, "base/main/manage_units.html", {
        "units": units,
        "courses": courses,
        "sort_by": sort_by,
        "order": order
    })


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
    

@require_POST
@login_required
@allowed_roles(["teacher"])
def delete_selected_units(request):
    unit_ids = request.POST.getlist("unit_ids")
    if unit_ids:
        deleted_count = Unit.objects.filter(id__in=unit_ids).delete()[0]
        if deleted_count:
            messages.success(request, f"Successfully deleted {deleted_count} unit(s).")
        else:
            messages.warning(request, "No units were deleted.")
    else:
        messages.warning(request, "No units selected for deletion.")
    return redirect("manage-units")

# Managing Topics
@login_required
@allowed_roles(["teacher"])
def manage_topics(request):
    courses = Course.objects.filter(teacher=request.user)
    sort_by = request.GET.get("sort_by", "updated")  # Default sort by updated
    order = request.GET.get("order", "desc")  # Default descending

    # Define valid sort fields
    valid_sort_fields = ["title", "description", "updated", "unit__title"]
    if sort_by not in valid_sort_fields:
        sort_by = "updated"

    # Apply sorting
    if order == "asc":
        topics = Topic.objects.all().select_related("unit").order_by(sort_by)
    else:
        topics = Topic.objects.all().select_related("unit").order_by(f"-{sort_by}")

    return render(request, "base/main/manage_topics.html", {
        "topics": topics,
        "courses": courses,
        "sort_by": sort_by,
        "order": order
    })

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


@require_POST
@login_required
@allowed_roles(["teacher"])
def delete_selected_topics(request):
    topic_ids = request.POST.getlist("topic_ids")
    if topic_ids:
        deleted_count = Topic.objects.filter(id__in=topic_ids).delete()[0]
        if deleted_count:
            messages.success(request, f"Successfully deleted {deleted_count} topic(s).")
        else:
            messages.warning(request, "No topics were deleted.")
    else:
        messages.warning(request, "No topics selected for deletion.")
    return redirect("manage-topics")