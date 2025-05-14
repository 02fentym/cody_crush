from django.urls import path
from . import views

urlpatterns = [
    # GENERIC
    path("", views.home, name="home"),

    path("login/", views.login_user, name="login"),
    path("register/", views.register_user, name="register-user"),
    path("logout/", views.logout_user, name = "logout"),

    path("course/<int:course_id>/", views.course, name="course"),

    # STUDENT
    path("activity/<int:activity_id>/start-quiz/", views.start_quiz, name="start-quiz"),
    path('quiz/<int:quiz_id>/activity/<int:activity_id>/take-quiz/', views.take_quiz, name='take-quiz'),
    path("quiz/results/<int:ac_id>/", views.quiz_results, name="quiz-results"),

    path("lessons/<lesson_id>/view/", views.view_lesson, name="view-lesson"),

    # TEACHER
    
    # deletion views
    path("course/<int:course_id>/delete/", views.delete_course, name="delete-course"),
    path("activity/delete/<int:activity_id>/", views.delete_activity, name="delete-activity"),

    # question uploading
    path("upload-questions/", views.upload_questions, name="upload-questions"),

    # quiz views
    path("topic/<int:topic_id>/create-quiz/", views.create_quiz, name="create-quiz"),

    # lesson views
    path("topic/<topic_id>/lesson/create/", views.create_lesson, name="create-lesson"),
    path("topic/<topic_id>/lesson/<int:lesson_id>/edit/", views.edit_lesson, name="edit-lesson"),

    # dmoj exercise views
    path("topic/<topic_id>/update_dmoj/", views.update_dmoj_exercises, name="update-dmoj-exercises"),

    
    # ADD CONTENT
    # Unit Creation
    path("unit-form/<int:course_id>/", views.get_unit_form, name="get_unit_form"),
    path("submit-unit-form/<int:course_id>/", views.submit_unit_form, name="submit_unit_form"),

    # Unit Deletion
    path("units/<int:unit_id>/delete/", views.delete_unit, name="delete_unit"),

    # Topic Creation
    path("topic-form/<int:unit_id>/", views.get_topic_form, name="get_topic_form"),
    path("submit-topic-form/<int:unit_id>/", views.submit_topic_form, name="submit_topic_form"),

    # Topic Deletion
    path("topics/<int:topic_id>/delete/", views.delete_topic, name="delete_topic"),

    # DMOJ Exercise Creation
    path("get_dmoj_form/<int:topic_id>/", views.get_dmoj_form, name="get_dmoj_form"),
    path("submit_dmoj_form/<int:topic_id>/", views.submit_dmoj_form, name="submit_dmoj_form"),

]
