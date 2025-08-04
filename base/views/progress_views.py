from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render
from base.decorators import allowed_roles
from base.models import Activity, ActivityCompletion, Course, User, StudentCourseEnrollment
from django.utils.timezone import localtime
from base.constants import ACTIVITY_TYPE_DISPLAY
from base.utils import get_all_courses


@login_required
def student_progress(request, course_id, student_id=None):
    if student_id and request.user.profile.role == "teacher":
        student = get_object_or_404(User, id=student_id)
    else:
        student = request.user

    # Get all courses this student is enrolled in (for sidebar)
    courses = get_all_courses("student", student)

    # Get the specific course
    enrollment = get_object_or_404(StudentCourseEnrollment, student=student, course_id=course_id)
    course = enrollment.course

    # Use stored values instead of recalculating
    score = enrollment.score
    progress = enrollment.progress

    # Get all activities in this course
    activities = (
        Activity.objects
        .filter(course_topic__course=course)
        .select_related("course_topic__unit", "course_topic__topic", "content_type")
        .order_by("course_topic__order", "order")
    )


    # Fetch all completions for the student in this course
    all_completions = (
        ActivityCompletion.objects
        .filter(student=student, activity__in=activities)
        .order_by("activity_id", "-score")  # highest score first per activity
    )

    # Keep only the highest score per activity
    completions = {}
    for ac in all_completions:
        if ac.activity_id not in completions:
            completions[ac.activity_id] = ac

    activity_rows = []
    for activity in activities:
        ac = completions.get(activity.id)

        model = activity.content_type.model
        if model == "quiztemplate":
            key = model  # for filtering
            display_type = ACTIVITY_TYPE_DISPLAY.get(f"{model}_{activity.content_object.question_type}", "Quiz")
        else:
            key = model
            display_type = ACTIVITY_TYPE_DISPLAY.get(key, model.title())


        activity_rows.append({
            "activity": activity,
            "course_unit": activity.course_topic.unit.title,
            "course_topic": activity.course_topic.topic.title,
            "type": key,  # used for filtering
            "display_type": display_type,  # shown in the table
            "weight": activity.weight,
            "completed": ac.completed if ac else False,
            "score": ac.score if ac else None,
            "date_completed": localtime(ac.date_completed) if ac and ac.date_completed else None,
        })

    # For grouping by unit in the UI
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




@login_required
@allowed_roles(["teacher"])
def student_list(request, course_id):
    # Sidebar course list
    courses = get_all_courses("teacher", request.user)

    # Target course
    course = get_object_or_404(Course, id=course_id)

    # Enrollments = all students in this course
    enrollments = (
        StudentCourseEnrollment.objects
        .select_related("student__profile")
        .filter(course=course)
    )

    # Count of activities in the course
    total_activities = Activity.objects.filter(
        course_topic__course=course
    ).count()

    rows = []
    for enrollment in enrollments:
        student = enrollment.student

        completions = ActivityCompletion.objects.filter(
            student=student,
            activity__course_topic__unit__courseunit__course=course
        )
        done = completions.filter(completed=True).values("activity_id").distinct().count()

        last_active = (
            completions.order_by("-date_completed").first().date_completed
            if completions.exists()
            else student.date_joined
        )

        rows.append({
            "student_id": student.id,
            "name": student.get_full_name(),
            "email": student.email,
            "progress": enrollment.progress,
            "score": enrollment.score,
            "completed": f"{done}/{total_activities}",
            "last_active": last_active,
        })

    return render(request, "base/main/students.html", {
        "courses": courses,
        "course": course,
        "rows": rows,
    })
