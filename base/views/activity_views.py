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


# Course Topic Addition



# Activity Deletion
@require_POST
@login_required(login_url="login")
@allowed_roles(["teacher"])
def delete_activity(request, activity_id):
    activity = get_object_or_404(Activity, id=activity_id)
    unit = activity.topic.unit

     # Delete the associated object, whether it's a lesson or quiz_template
    activity.content_object.delete()

    # Delete the Activity itself too
    activity.delete()

    messages.success(request, "Activity deleted successfully!")
    return render(request, "base/partials/topic_list.html", {"unit": unit})

