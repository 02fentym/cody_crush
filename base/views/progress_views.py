from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render
from base.decorators import allowed_roles
from base.models import Activity, ActivityCompletion

@login_required
@allowed_roles(["student"])
def progress(request, course_id):
    student = request.user
    courses = student.enrolled_courses.all()
    course = get_object_or_404(student.enrolled_courses, id=course_id)

    percent = get_course_progress(student, course)

    context = {
        "courses": courses,
        "course": course,
        "percent": percent
    }

    return render(request, "base/main/progress.html", context)

def get_course_progress(student, course):
    all_activities = Activity.objects.filter(
        course_topic__unit__courseunit__course=course
    ).select_related("course_topic", "content_type")

    completions = ActivityCompletion.objects.filter(
        student=student,
        completed=True,
        score__isnull=False,
        activity__in=all_activities
    ).select_related("activity", "activity__content_type")

    earned = 0
    for ac in completions:
        model = ac.activity.content_type.model
        if model == "quiztemplate":
            earned_val = ac.score  # already percentage-based
        else:
            earned_val = ac.score  # DMOJ, raw marks out of activity.weight

        earned += min(earned_val, ac.activity.weight)

        print(
            f"Activity: {ac.activity}, Type: {model}, "
            f"Weight: {ac.activity.weight}, Score: {ac.score}, Value: {earned_val}"
        )

    total = sum(a.weight for a in all_activities)
    percent = round((earned / total) * 100, 1) if total > 0 else 0
    return percent
