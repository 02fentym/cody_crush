from django.urls import path
from . import views

urlpatterns = [
    # GENERIC
    path("", views.home, name="home"),

    path("login/", views.login_user, name="login"),
    path("register/", views.register_user, name="register-user"),
    path("logout/", views.logout_user, name = "logout"),

    path("course/<int:course_id>/", views.course, name="course"),
    path("course/<int:course_id>/unit/<int:unit_id>/", views.unit, name="unit"),
    path("course/<int:course_id>/unit/<int:unit_id>/topic/<int:topic_id>/", views.topic, name="topic"),

    # STUDENT
    path("activity/<int:activity_id>/start-quiz/", views.start_quiz, name="start-quiz"),
    path('quiz/<int:quiz_id>/activity/<int:activity_id>/take-quiz/', views.take_quiz, name='take-quiz'),
    path("quiz/results/<int:quiz_id>/", views.quiz_results, name="quiz-results"),

    path("lessons/<lesson_id>/view/", views.view_lesson, name="view-lesson"),

    # TEACHER
    
    # deletion views
    path("course/<int:course_id>/delete/", views.delete_course, name="delete-course"),
    path("course/<int:course_id>/unit/<int:unit_id>/delete/", views.delete_unit, name="delete-unit"),
    path("course/<int:course_id>/unit/<int:unit_id>/topic/<int:topic_id>/delete/", views.delete_topic, name="delete-topic"),
    path("activity/delete/<int:activity_id>/", views.delete_activity, name="delete-activity"),

    # question uploading
    path("upload-questions/", views.upload_questions, name="upload-questions"),

    # quiz views
    path("topic/<int:topic_id>/create-quiz/", views.create_quiz, name="create-quiz"),

    # lesson views
    path("topics/<topic_id>/lesson/create/", views.create_lesson, name="create-lesson"),
    path("topics/<topic_id>/lesson/<int:lesson_id>/edit/", views.edit_lesson, name="edit-lesson"),

    # dmoj exercise views
    path("topic/<topic_id>/create_dmoj_exercise/", views.create_dmoj_exercise, name="create-dmoj-exercise"),
]