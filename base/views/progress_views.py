from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render
from base.decorators import allowed_roles
from base.models import Activity, ActivityCompletion, Course, User
from django.utils.timezone import localtime
from base.constants import WEIGHTING_DISPLAY_NAMES


@login_required
def student_progress(request, course_id, student_id=None):
    if student_id and request.user.profile.role == "teacher":
        student = get_object_or_404(User, id=student_id)
    else:
        student = request.user

    courses = student.enrolled_courses.all()
    
    # Get course from enrolled_courses if student, otherwise check membership
    if request.user.profile.role == "student":
        course = get_object_or_404(student.enrolled_courses, id=course_id)
    else:
        course = get_object_or_404(Course, id=course_id)


    score = get_course_score(student, course)  # weighted average

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
    progress = get_course_progress(student, course)

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
        "student": student,
        "courses": courses,
        "course": course,
        "score": score,
        "progress": progress,
        "activity_rows": activity_rows,
        "course_units": course_units
    }

    return render(request, "base/main/progress.html", context)


def get_course_score(student, course):
    completions = (
        ActivityCompletion.objects
        .filter(
            student=student,
            completed=True,
            score__isnull=False,
            activity__course_topic__unit__courseunit__course=course
        )
        .select_related("activity", "activity__content_type")
        .order_by("activity_id", "-score")  # Order so highest comes first
    )

    # Keep only highest score per activity
    highest_per_activity = {}
    for ac in completions:
        if ac.activity_id not in highest_per_activity:
            highest_per_activity[ac.activity_id] = ac  # first one is highest due to ordering

    earned = 0
    completed_weight = 0

    for ac in highest_per_activity.values():
        if ac.activity.weight:  # skip if None
            earned += ac.score
            completed_weight += ac.activity.weight

    if completed_weight == 0:
        return 0

    return round((earned / completed_weight) * 100, 1)



def get_course_progress(student, course):
    total_activities = Activity.objects.filter(
        course_topic__course=course
    ).count()

    if total_activities == 0:
        return 0

    completed_activities = ActivityCompletion.objects.filter(
        student=student,
        activity__course_topic__unit__courseunit__course=course,
        completed=True
    ).values("activity_id").distinct().count()

    return round((completed_activities / total_activities) * 100, 1)


@login_required
@allowed_roles(["teacher"])
def student_list(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    students = course.students.select_related("profile").all()

    # ✅ Count all activities for this course
    total_activities = Activity.objects.filter(
        course_topic__course=course
    ).count()

    rows = []
    for student in students:
        mark = get_course_score(student, course)

        completions = ActivityCompletion.objects.filter(
            student=student,
            activity__course_topic__unit__courseunit__course=course
        )
        done = completions.filter(completed=True).values("activity_id").distinct().count()

        progress = get_course_progress(student, course)

        if completions.exists():
            last_active = completions.order_by("-date_completed").first().date_completed
        else:
            last_active = student.date_joined

        rows.append({
            "student_id": student.id,
            "name": student.get_full_name(),
            "email": student.email,
            "progress": progress,
            "score": mark,
            "completed": f"{done}/{total_activities}",
            "last_active": last_active,
        })

    return render(request, "base/main/students.html", {
        "course": course,
        "rows": rows,
        "active_tab": "overview"
    })

