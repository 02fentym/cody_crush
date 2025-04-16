from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),

    path("login/", views.login_user, name="login"),
    path("register/", views.register_user, name="register-user"),
    path("logout/", views.logout_user, name = "logout"),

    path("quiz/start/<int:lesson_id>/", views.start_quiz, name="start-quiz"),
    path("quiz/take/<int:quiz_id>/", views.take_quiz, name="take-quiz"),
    path("quiz/results/<int:quiz_id>/", views.quiz_results, name="quiz-results"),
]