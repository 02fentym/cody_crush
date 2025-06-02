from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.db.models import Max
from django.contrib.contenttypes.models import ContentType

from base.decorators import allowed_roles
from base.models import (
    Course, CourseUnit, Unit, Topic, Activity,
    DmojExercise
)
from base.forms import (
    CourseUnitForm, TopicForm, DmojForm
)
from base.utils import fetch_dmoj_metadata_from_url


# Activity Deletion
@login_required
@allowed_roles(["teacher"])
@require_POST
def delete_activity(request, activity_id):
    activity = get_object_or_404(Activity, id=activity_id)
    activity.delete()
    return HttpResponse("")  # HTMX will just remove the element

