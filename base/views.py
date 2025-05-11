from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from .models import (Unit, Topic, Quiz, Answer, Profile, Course, QuizTemplate, Activity, Lesson, 
    MultipleChoiceQuestion, TracingQuestion, DmojExercise, ActivityCompletion
)
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from .forms import UserForm, CourseForm, UnitForm, TopicForm, EnrollmentPasswordForm, LessonForm, DmojForm
from django.contrib.contenttypes.models import ContentType
from .decorators import allowed_roles
from .utils import fetch_dmoj_metadata_from_url, fetch_dmoj_user_data
from django.utils import timezone
from datetime import timedelta
from django.db.models import Max

import csv, io, markdown, re

from markdown.extensions.fenced_code import FencedCodeExtension


###################### GENERIC VIEWS

def login_user(request):
    page = "login"

    if request.user.is_authenticated:
        return redirect("home")

    if request.method == "POST":
        username = request.POST.get("username").lower()
        password = request.POST.get("password")
        
        try:
            user = User.objects.get(username=username)
        except:
            messages.error(request, "User does not exist")
            return redirect("home")
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect("home")
        else:
            messages.error(request, "Password is incorrect")
            return redirect("home")

    context = {"page": page}
    return render(request, "base/login.html", context)


def register_user(request):
    form = UserForm()

    if request.method == "POST":
        form = UserForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("home")
        else:
            messages.error(request, "An error occurred during registration")

    context = {"page": "register", "form": form}
    return render(request, "base/register.html", context)



def logout_user(request):
    logout(request)
    return redirect("login")


'''
@login_required(login_url="login")
def home_selector(request):
    role = request.user.profile.role

    if role == "teacher":
        return redirect("home")
    elif role == "student":
        return redirect("student-home")
    else:
        return redirect("login")  # or raise an error
'''

@login_required(login_url="login")
def home(request):
    courses = get_all_courses(request.user.profile.role, request.user)
    
    if request.method == "POST":
        form_type = request.POST.get("form_type")

        if form_type == "course":
            course_form = CourseForm(request.POST)
            if course_form.is_valid():
                course = course_form.save(commit=False)
                course.teacher = request.user
                course.language = request.POST.get("language")
                course.save()
                messages.success(request, "Course created successfully!")
                return redirect("home")
        elif form_type == "password":
            password_form = EnrollmentPasswordForm(request.POST)
            enrollment_password = request.POST.get("enrollment_password")

            try:
                course = Course.objects.get(enrollment_password=enrollment_password)
                course.students.add(request.user)
                messages.success(request, f"You have been enrolled in {course.title}!")
            except Course.DoesNotExist:
                messages.error(request, "Invalid enrollment password. Please try again.")

            return redirect("home")
    else:
        course_form = CourseForm()
        password_form = EnrollmentPasswordForm()

    context = {"courses": courses, "course_form": course_form, "password_form": password_form}
    return render(request, "base/home.html", context)


# Helper function to get all courses
def get_all_courses(role, user):
    if role == "student":
        courses = user.enrolled_courses.all()
    else:
        courses = Course.objects.filter(teacher=user)
    return courses
        

###################### STUDENT VIEWS

@allowed_roles(["student"])
@login_required(login_url="login")
def start_quiz(request, activity_id):
    activity = get_object_or_404(Activity, id=activity_id)
    topic = activity.topic
    template = activity.content_object

    # Determine the question model
    if template.question_type == "multiple_choice":
        model = MultipleChoiceQuestion
    elif template.question_type == "tracing":
        model = TracingQuestion
    else:
        messages.error(request, "Unsupported question type.")
        return redirect("topic", topic.unit.course.id, topic.unit.id, topic.id)

    # Get content type for the selected question model
    content_type = ContentType.objects.get_for_model(model)

    # Random questions
    questions = model.objects.filter(topic=topic).order_by("?")[:template.question_count]

    # Create Quiz
    quiz = Quiz.objects.create(
        student=request.user,
        topic=topic,
        question_type=template.question_type
    )

    # Link questions using the bridge table
    from .models import QuizQuestion
    for question in questions:
        QuizQuestion.objects.create(
            quiz=quiz,
            content_type=content_type,
            object_id=question.id
        )

    return redirect("take-quiz", quiz_id=quiz.id, activity_id=activity.id)


@allowed_roles(["student"])
@login_required(login_url="login")
def take_quiz(request, quiz_id, activity_id):
    quiz = get_object_or_404(Quiz, id=quiz_id, student=request.user)
    activity = get_object_or_404(Activity, id=activity_id)
    question_type = quiz.question_type
    quiz_questions = quiz.quiz_questions.all()  # this gives access to both question and bridge

    if request.method == "POST":
        # Create the ActivityCompletion so we can link answers to it
        previous_attempts = ActivityCompletion.objects.filter(student=request.user, activity=activity).count()

        ac = ActivityCompletion.objects.create(
            student=request.user,
            activity=activity,
            completed=False,
            attempt_number=previous_attempts + 1,
            date_completed=timezone.now()
        )

        correct_count = 0
        total = quiz_questions.count()

        for qq in quiz_questions:
            question = qq.question
            user_input = request.POST.get(f'q{question.id}')

            if user_input:
                # Default to False in case we can't validate
                is_correct = False

                if question_type == "multiple_choice":
                    is_correct = user_input == question.correct_choice
                elif question_type == "tracing":
                    student_output = normalize_output(user_input)
                    correct_output = normalize_output(question.expected_output)
                    is_correct = student_output == correct_output

                # Save the answer
                Answer.objects.create(
                    quiz=quiz,
                    quiz_question=qq,
                    activity_completion=ac,
                    selected_choice=user_input if question_type == "multiple_choice" else None,
                    text_answer=user_input if question_type == "tracing" else None,
                    is_correct=is_correct
                )

                if is_correct:
                    correct_count += 1

        # Save grade
        grade = (correct_count / total) * 100
        quiz.grade = round(grade, 2)
        quiz.save()

        # Update the activity_completion to mark it complete + save the score
        ac.completed = True
        ac.score = quiz.grade
        ac.save()

        return redirect("quiz-results", ac.id)

    # GET request → show the quiz
    context = {"quiz": quiz, "questions": [qq.question for qq in quiz_questions]}
    return render(request, "base/quiz.html", context)



# Helper function to normalize output for tracing questions
def normalize_output(text):
    lines = text.strip().splitlines()
    return "\n".join(line.strip() for line in lines)


@allowed_roles(["student"])
@login_required(login_url="login")
def quiz_results(request, ac_id):
    ac = get_object_or_404(ActivityCompletion, id=ac_id, student=request.user)
    activity = ac.activity
    quiz_template = activity.content_object
    answers = Answer.objects.filter(activity_completion=ac).select_related('quiz_question')

    context = {
        "activity_completion": ac,
        "activity": activity,
        "quiz_template": quiz_template,
        "answers": answers,
    }

    return render(request, "base/quiz_results.html", context)





###################### TEACHER VIEWS

def course(request, course_id):
    user = request.user
    courses = get_all_courses(user.profile.role, user)

    if user.profile.role == "teacher":
        qs = Course.objects.filter(id=course_id, teacher=user)
    else:
        qs = Course.objects.filter(id=course_id, students=user)

    course = get_object_or_404(qs)

    unit_form = UnitForm()
    password_form = EnrollmentPasswordForm(instance=course)

    # Handle unit creation, course password update and unit deletion
    if request.method == "POST":
        form_type = request.POST.get("form_type")

        # Unit creation
        if form_type == "unit":
            unit_form = UnitForm(request.POST)
            if unit_form.is_valid():
                unit = unit_form.save(commit=False)
                unit.course = course
                last_order = course.unit_set.aggregate(Max('order'))['order__max'] or 0
                unit.order = last_order + 1
                unit.save()
                messages.success(request, "Unit created successfully!")
                return redirect("course", course_id=course_id)

        # Course password update
        elif form_type == "password":
            password_form = EnrollmentPasswordForm(request.POST, instance=course)
            if password_form.is_valid():
                password_form.save()
                messages.success(request, "Enrollment password updated!")
                return redirect("course", course_id=course_id)

        # Unit deletion
        elif form_type == "delete_unit":
            unit_id = request.POST.get("unit_id")
            unit_to_delete = get_object_or_404(Unit, id=unit_id, course=course)
            unit_to_delete.delete()
            messages.success(request, "Unit deleted successfully!")
            return redirect("course", course_id=course_id)
        
        # Topic creation
        elif form_type == "topic":
            unit_id = request.POST.get("unit_id")
            unit = get_object_or_404(Unit, id=unit_id, course=course)

            topic_form = TopicForm(request.POST)
            if topic_form.is_valid():
                topic = topic_form.save(commit=False)
                topic.unit = unit

                # Set topic order nicely
                last_order = unit.topic_set.aggregate(Max('order'))['order__max'] or 0
                topic.order = last_order + 1

                topic.save()
                messages.success(request, "Topic created successfully!")
                return redirect("course", course_id=course_id)
        
        # Topic deletion
        elif form_type == "delete_topic":
            topic_id = request.POST.get("topic_id")
            topic_to_delete = get_object_or_404(Topic, id=topic_id, unit__course=course)
            topic_to_delete.delete()
            messages.success(request, "Topic deleted successfully!")
            return redirect("course", course_id=course_id)
        

    # Prefetch Topics and Activities inside Topics
    units = course.unit_set.prefetch_related('topic_set__activity_set').all()

    context = {"courses": courses, "course": course, "units": units, "unit_form": unit_form, "password_form": password_form,}
    return render(request, "base/course.html", context)


def delete_course(request, course_id):
    course = get_object_or_404(Course, id=course_id, teacher=request.user)
    course.delete()
    messages.success(request, "Course deleted successfully!")
    return redirect("home")


def delete_unit(request, course_id, unit_id):
    unit = get_object_or_404(Unit, id=unit_id, course__id=course_id)
    unit.delete()
    messages.success(request, "Unit deleted successfully!")
    return redirect("course", course_id=course_id)


def delete_topic(request, course_id, unit_id, topic_id):
    topic = get_object_or_404(Topic, id=topic_id, unit__id=unit_id, unit__course__id=course_id)
    topic.delete()
    messages.success(request, "Topic deleted successfully!")
    return redirect("unit", course_id=course_id, unit_id=unit_id)


def create_quiz(request, topic_id):
    topic = get_object_or_404(Topic, id=topic_id)
    course_id = topic.unit.course.id
    
    question_count = int(request.POST.get("question_count", 5)) # Default to 5 if not provided
    question_type = request.POST.get("question_type")

    # Check if there are enough questions available for selected type
    QUESTION_TYPE_MAP = {
        "multiple_choice": MultipleChoiceQuestion,
        "tracing": TracingQuestion,
    }
    question_model = QUESTION_TYPE_MAP.get(question_type)
    available_count = question_model.objects.filter(topic=topic).count()
    if available_count < question_count:
        messages.error(request, f"Only {available_count} questions available for this topic.")
        return redirect("course", course_id=course_id)

    
    quiz_template = QuizTemplate.objects.create(
        topic=topic,
        question_count=question_count,
        question_type=question_type
    )

    Activity.objects.create(
        topic=topic,
        order=topic.activity_set.count() + 1,
        content_type=ContentType.objects.get_for_model(quiz_template),
        object_id=quiz_template.id
    )

    messages.success(request, "Quiz created successfully!")

    return redirect("course", course_id=course_id)


def delete_activity(request, activity_id):
    activity = get_object_or_404(Activity, id=activity_id)

     # Delete the associated object, whether it's a lesson or quiz_template
    activity.content_object.delete()

    # Delete the Activity itself too
    activity.delete()

    messages.success(request, "Activity deleted successfully!")
    return redirect("course", course_id=activity.topic.unit.course.id)


@allowed_roles(["teacher"])
@login_required(login_url="login")
def upload_questions(request):
    errors = []

    if request.method == "POST":

        # Step 1: Open csv file
        file = request.FILES["file"]
        data = file.read().decode("utf-8")
        csv_file = io.StringIO(data)
        reader = csv.DictReader(csv_file)

        for i, row in enumerate(reader, start=2):
            # Step 2: Validate row data
            result = question_data_validation(i, row)
            if result:
                errors.append(result)
                continue

            # Step 3: Get topic and question type
            topic = Topic.objects.get(id=row["topic_id"])
            question_type = row["question_type"].strip().lower()

            try:
                # Step 3: Create appropriate question subclass
                if question_type == "multiple_choice":
                    MultipleChoiceQuestion.objects.create(
                        topic=topic,
                        prompt=row["prompt"],
                        choice_a=row["choice_a"],
                        choice_b=row["choice_b"],
                        choice_c=row["choice_c"],
                        choice_d=row["choice_d"],
                        correct_choice=row["correct_choice"].lower(),
                        explanation=row["explanation"],
                        language=row.get("language", "")
                    )
                elif question_type == "tracing":
                    print(f"Row {i} expected_output:", repr(row["expected_output"]))
                    TracingQuestion.objects.create(
                        topic=topic,
                        prompt=row["prompt"],
                        expected_output=row["expected_output"],
                        explanation=row["explanation"],
                        language=row.get("language", "")
                    )
            except Exception as e:
                errors.append(f"Row {i}: Failed to create question. Error: {str(e)}")

        # Final message
        if not errors:
            messages.success(request, "Questions uploaded successfully.")
        else:
            messages.error(request, f"{len(errors)} errors occurred during upload.")
            for err in errors:
                messages.error(request, err)

    return redirect("home")


# Helper function to validate question data
def question_data_validation(i, row):
    # Validate that the topic exists
    topic_id = row.get("topic_id")
    try:
        Topic.objects.get(id=topic_id)
    except Topic.DoesNotExist:
        return f"Row {i}: topic ID {topic_id} does not exist."

    # Validate question type
    question_type = row.get("question_type", "").strip().lower()
    if question_type not in ["multiple_choice", "tracing"]:
        return f"Row {i}: Invalid or missing question_type."

    # Validate required fields based on question type
    if question_type == "multiple_choice":
        required_fields = ["prompt", "choice_a", "choice_b", "choice_c", "choice_d", "correct_choice", "explanation", "language", "topic_id"]
    elif question_type == "tracing":
        required_fields = ["prompt", "expected_output", "explanation", "language", "topic_id"]

    # Validate required fields for the given type
    for field in required_fields:
        if not row.get(field):
            return f"Row {i}: Missing value for '{field}' ({question_type} question)."

    return ""  # If all is well



def create_lesson(request, topic_id):
    topic = get_object_or_404(Topic, id=topic_id)
    form = LessonForm()

    if request.method == "POST":
        form = LessonForm(request.POST)
        if form.is_valid():
            lesson = form.save(commit=False)
            lesson.save()

            Activity.objects.create(
                topic=topic,
                order=topic.activity_set.count() + 1,
                content_type=ContentType.objects.get_for_model(lesson),
                object_id=lesson.id
            )

            return redirect("course", topic.unit.course.id)
        else:
            messages.error(request, "Please fix the errors below.")

        
    context = {"topic": topic, "form": form, "is_edit": False}
    return render(request, "base/create_edit_lesson.html", context)


def edit_lesson(request, topic_id, lesson_id):
    lesson = Lesson.objects.get(id=lesson_id)
    topic = Topic.objects.get(id=topic_id)
    form = LessonForm(instance=lesson)

    if request.method == "POST":
        form = LessonForm(request.POST, instance=lesson)
        if form.is_valid():
            form.save()
            messages.success(request, "Lesson updated successfully!")
            return redirect("course", topic.unit.course.id)

    context = {"form": form, "is_edit": True}
    return render(request, "base/create_edit_lesson.html", context)


@allowed_roles(["student"])
@login_required(login_url="login")
def view_lesson(request, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)
    activity = Activity.objects.get(content_type__model="lesson", object_id=lesson.id)
    course_language = activity.topic.unit.course.language.lower()  # like "python", "java"

    if request.method == "POST":
        if 'mark_as_complete' in request.POST:
            ActivityCompletion.objects.update_or_create(
                student=request.user,
                activity=activity,
                defaults={'completed': True, 'date_completed': timezone.now()}
            )
        else:
            completion = ActivityCompletion.objects.filter(student=request.user, activity=activity).first()
            if completion:
                completion.completed = False
                date_completed = None
                completion.save()

        return redirect('view-lesson', lesson_id=lesson.id)

    # Step 1: Parse the Markdown (handle fenced code blocks)
    lesson_html = markdown.markdown(
        lesson.content,
        extensions=[FencedCodeExtension()]
    )

    # Step 2: Post-process to add language class
    lesson_html = re.sub(r'<pre><code>', f'<pre><code class="language-{course_language}">', lesson_html)
    lesson_html = re.sub(r'(?<!<pre>)<code>', f'<code class="language-{course_language}">', lesson_html)

    # Step 3: Get completion status
    completion = ActivityCompletion.objects.filter(student=request.user, activity=activity).first()
    completed = completion.completed if completion else False

    context = {
        "lesson": lesson,
        "lesson_html": lesson_html,
        "activity": activity,
        "completed": completed,
    }
    return render(request, "base/view_lesson.html", context)


def create_dmoj_exercise(request, topic_id):
    topic = get_object_or_404(Topic, id=topic_id)
    course = topic.unit.course
    
    if request.method == "POST":
        url = request.POST.get("url")
        metadata = fetch_dmoj_metadata_from_url(url)
        
        if metadata:
            dmoj_exercise = DmojExercise.objects.create(
                title=metadata['title'],
                url=url,
                problem_code=metadata['problem_code'],
                points=metadata['points']
            )

            Activity.objects.create(
                topic=topic,
                order=topic.activity_set.count() + 1,
                content_type=ContentType.objects.get_for_model(dmoj_exercise),
                object_id=dmoj_exercise.id
            )

            messages.success(request, "DMOJ exercise created successfully!")
        else:
            messages.error(request, "Failed to fetch DMOJ metadata. Please check the URL.")

    
    return redirect("course", course_id=course.id)


def update_dmoj_exercises(request, topic_id):
    topic = get_object_or_404(Topic, id=topic_id)
    profile = request.user.profile
    now = timezone.now()
    cooldown_minutes = 2

    # Check if cooldown period has passed
    if now - profile.last_dmoj_update < timedelta(minutes=cooldown_minutes):
        wait_time = cooldown_minutes - (now - profile.last_dmoj_update).seconds // 60
        messages.error(request, f"Please wait {wait_time} more minutes before refreshing again.")
        return redirect("topic", course_id=topic.unit.course.id, unit_id=topic.unit.id, topic_id=topic_id)
    

    # Fetch DMOJ user solved problems (list of problem codes)
    solved_problems = fetch_dmoj_user_data(request.user.profile.dmoj_username)

    # Fetch ALL DMOJ exercise activities across the system
    dmojexercise_type = ContentType.objects.get_for_model(DmojExercise)
    activities = Activity.objects.filter(content_type=dmojexercise_type)

    for activity in activities:
        dmoj_exercise = activity.content_object
        if dmoj_exercise.problem_code in solved_problems:

            completion = ActivityCompletion.objects.filter(student=request.user, activity=activity, completed=True).first()

            if not completion:
                ActivityCompletion.objects.update_or_create(
                    student=request.user,
                    activity=activity,
                    defaults={'completed': True, 'date_completed': now}
                )

    profile.last_dmoj_update = now
    profile.save()

    messages.success(request, "DMOJ exercises successfully refreshed!")
    return redirect("topic", course_id=topic.unit.course.id, unit_id=topic.unit.id, topic_id=topic_id)