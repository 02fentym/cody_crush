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

    # Course Enrolment
    path("enrolment-form/", views.get_enrolment_form, name="get-enrolment-form"),
    path("enrol/", views.enrol_in_course, name="enrol-in-course"),

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


    # Unit Deletion


    # DMOJ Exercise Creation
    path("get_dmoj_form/<int:topic_id>/", views.get_dmoj_form, name="get-dmoj-form"),
    path("submit_dmoj_form/<int:topic_id>/", views.submit_dmoj_form, name="submit-dmoj-form"),

    # Quiz Creation
    path("topic/<int:topic_id>/quiz-form/", views.get_quiz_form, name="get-quiz-form"),
    path("topic/<int:topic_id>/submit-quiz/", views.submit_quiz_form, name="submit-quiz-form"),
    


    # URLS for course_unit_views.py
    path("course/<int:course_id>/get-course-unit-form/", views.get_course_unit_form, name="get-course-unit-form"),
    path("submit-course-unit-form/", views.submit_course_unit_form, name="submit-course-unit-form"),
    path("delete-course-unit/<int:course_unit_id>/", views.delete_course_unit, name="delete-course-unit"),




    # URLS for course_topic_views.py
    path("get-course-topic-form/<int:unit_id>/", views.get_course_topic_form, name="get-course-topic-form"),
    path("submit-course-topic-form/", views.submit_course_topic_form, name="submit-course-topic-form"),
    path("delete-course-topic/<int:course_topic_id>/", views.delete_course_topic, name="delete-course-topic"),


    # URLS for unit_topic_management_views.py
    # Units
    path("manage-units/", views.manage_units, name="manage-units"),
    path("get-unit-form/", views.get_unit_form, name="get-unit-form"),
    path("submit-unit-form-manage/", views.submit_unit_form_manage, name="submit-unit-form-manage"),

    # Topics
    path("manage-topics/", views.manage_topics, name="manage-topics"),
    path("get-topic-form/", views.get_topic_form, name="get-topic-form"),
    path("submit-topic-form/", views.submit_topic_form, name="submit-topic-form"),

]
