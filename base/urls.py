from django.urls import path
from . import views

urlpatterns = [
    # GENERIC
    path("", views.home, name="home"),

    path("login/", views.login_user, name="login"),
    path("register/", views.register_user, name="register-user"),
    path("logout/", views.logout_user, name = "logout"),


    # STUDENT
    path("course/<int:course_id>/unit/<int:unit_id>/topic/<int:topic_id>/start-quiz/", views.start_quiz, name="start-quiz"),
    path("activity/<int:activity_id>/start-quiz/", views.start_quiz, name="start-quiz"),
    path("quiz/<int:quiz_id>/take-quiz/", views.take_quiz, name="take-quiz"),
    path("quiz/results/<int:quiz_id>/", views.quiz_results, name="quiz-results"),

    # TEACHER
    path("course/<int:course_id>/", views.course, name="course"),
    path("course/<int:course_id>/delete/", views.delete_course, name="delete-course"),

    path("course/<int:course_id>/unit/<int:unit_id>/", views.unit, name="unit"),
    path("course/<int:course_id>/unit/<int:unit_id>/delete/", views.delete_unit, name="delete-unit"),

    path("course/<int:course_id>/unit/<int:unit_id>/topic/<int:topic_id>/", views.topic, name="topic"),
    path("course/<int:course_id>/unit/<int:unit_id>/topic/<int:topic_id>/delete/", views.delete_topic, name="delete-topic"),

    path("upload-questions/", views.upload_questions, name="upload-questions"),

    path("activity/delete/<int:activity_id>/", views.delete_activity, name="delete-activity"),

    path("topic/<int:topic_id>/create-quiz/", views.create_quiz, name="create-quiz"),
]