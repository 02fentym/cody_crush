from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.db.models import Max

from base.decorators import allowed_roles
from base.models import Unit, Topic
from base.forms import TopicForm


@login_required(login_url="login")
@allowed_roles(["teacher"])
def get_topic_form(request, unit_id):
    unit = get_object_or_404(Unit, id=unit_id)
    form = TopicForm()
    context = {"form": form, "unit": unit}
    return render(request, "base/partials/topic_form.html", context)

@require_POST
@login_required(login_url="login")
@allowed_roles(["teacher"])
def submit_topic_form(request, unit_id):
    unit = get_object_or_404(Unit, id=unit_id)
    form = TopicForm(request.POST)

    if form.is_valid():
        topic = form.save(commit=False)
        topic.unit = unit
        topic.order = (unit.topic_set.aggregate(Max("order"))["order__max"] or 0) + 1
        topic.save()
        topics = unit.topic_set.all()
        return render(request, "base/partials/topic_list.html", {"topics": topics, "unit": unit})

    return render(request, "base/partials/topic_form.html", {"form": form, "unit": unit})

# Course Topic Deletion
@require_POST
@login_required
@allowed_roles(["teacher"])
def delete_topic(request, topic_id):
    topic = get_object_or_404(Topic, id=topic_id, unit__course__teacher=request.user)
    unit = topic.unit
    topic.delete()

    topics = unit.topic_set.all()
    return render(request, "base/partials/topic_list.html", {"topics": topics, "unit": unit})