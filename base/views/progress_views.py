from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render
from base.decorators import allowed_roles
from base.models import Activity, ActivityCompletion, Course
from django.utils.timezone import localtime
from base.constants import WEIGHTING_DISPLAY_NAMES


@login_required
@allowed_roles(["student"])
def progress(request, course_id):
    student = request.user
    courses = student.enrolled_courses.all()
    course = get_object_or_404(student.enrolled_courses, id=course_id)

    mark = get_course_mark(student, course)  # weighted average

    activities = (
        Activity.objects
        .filter(course_topic__unit__courseunit__course=course)
        .select_related("course_topic__unit", "course_topic__topic", "content_type")
        .order_by("course_topic__order", "order")
    )

    completions = {
        ac.activity_id: ac
        for ac in ActivityCompletion.objects.filter(student=student, activity__in=activities)
    }

    # Compute progress
    total_activities = len(activities)
    completed_count = sum(1 for ac in completions.values() if ac.completed)
    progress = round((completed_count / total_activities) * 100, 1) if total_activities > 0 else 0

    activity_rows = []
    for activity in activities:
        ac = completions.get(activity.id)

        model = activity.content_type.model
        if model == "quiztemplate":
            quiz_obj = activity.content_object
            key = f"{model}_{quiz_obj.question_type}"
        else:
            key = model

        display_type = WEIGHTING_DISPLAY_NAMES.get(key, model.title())


        activity_rows.append({
            "activity": activity,
            "course_unit": activity.course_topic.unit.title,
            "course_topic": activity.course_topic.topic.title,
            "type": display_type,
            "weight": activity.weight,
            "completed": ac.completed if ac else False,
            "score": ac.score if ac else None,
            "date_completed": localtime(ac.date_completed) if ac and ac.date_completed else None,
        })

    course_units = (
        course.coursetopic_set
        .select_related("unit")
        .order_by("unit__title")
        .values_list("unit__title", flat=True)
        .distinct()
    )


    context = {
        "courses": courses,
        "course": course,
        "mark": mark,
        "progress": progress,
        "activity_rows": activity_rows,
        "course_units": course_units
    }

    return render(request, "base/main/progress.html", context)


def get_course_mark(student, course):
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
    completed_weight = 0

    for ac in completions:
        earned += ac.score
        completed_weight += ac.activity.weight

    if completed_weight == 0:
        return 0

    return round((earned / completed_weight) * 100, 1)


@login_required
@allowed_roles(["teacher"])
def student_list(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    students = course.students.select_related("profile").all()

    rows = []
    for student in students:
        mark = get_course_mark(student, course)

        completions = ActivityCompletion.objects.filter(
            student=student,
            activity__course_topic__unit__courseunit__course=course
        )
        total = completions.count()
        done = completions.filter(completed=True).count()
        percent = round((done / total) * 100) if total > 0 else 0

        # FIXED: use a valid field
        last_active = completions.order_by("-date_completed").first().date_completed if completions else None


        rows.append({
            "name": student.get_full_name(),
            "email": student.email,
            "progress": percent,
            "score": mark,
            "completed": f"{done}/{total}",
            "last_active": last_active,
        })

    return render(request, "base/main/students.html", {
        "course": course,
        "rows": rows,
        "active_tab": "overview"
    })
