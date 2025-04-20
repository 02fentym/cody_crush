from django.urls import path
from . import views

urlpatterns = [
    path("", views.home_selector, name="home"),
    path("teacher/", views.teacher_home, name="teacher-home"),
    path("student/", views.student_home, name="student-home"),

    path("login/", views.login_user, name="login"),
    path("register/", views.register_user, name="register-user"),
    path("logout/", views.logout_user, name = "logout"),


    # student
    path("quiz/start/<int:topic_id>/", views.start_quiz, name="start-quiz"),
    path("quiz/take/<int:quiz_id>/", views.take_quiz, name="take-quiz"),
    path("quiz/results/<int:quiz_id>/", views.quiz_results, name="quiz-results"),

    # teacher
    
    path("course/<int:course_id>/", views.course, name="course"),
    path("course/<int:course_id>/unit/<int:unit_id>/", views.unit, name="unit"),

    path("course/<int:course_id>/unit/<int:unit_id>/topic/<int:topic_id>/", views.topic, name="topic"),
    path("upload-questions/", views.upload_questions, name="upload-questions"),
]