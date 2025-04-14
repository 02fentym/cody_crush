from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("quiz/start/<int:lesson_id>/", views.start_quiz, name="start-quiz"),
    path("quiz/take/<int:quiz_id>/", views.take_quiz, name="take-quiz"),
]