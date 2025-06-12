from django.urls import path
from . import views

urlpatterns = [
### URLS for activity_views.py
    path("activity/<int:activity_id>/delete/", views.delete_activity, name="delete-activity"),


### URLS for course_topic_views.py
    path("get-course-topic-form/<int:unit_id>/", views.get_course_topic_form, name="get-course-topic-form"),
    path("submit-course-topic-form/", views.submit_course_topic_form, name="submit-course-topic-form"),
    path("delete-course-topic/<int:course_topic_id>/", views.delete_course_topic, name="delete-course-topic"),


### URLS for course_unit_views.py
    path("course/<int:course_id>/get-course-unit-form/", views.get_course_unit_form, name="get-course-unit-form"),
    path("submit-course-unit-form/", views.submit_course_unit_form, name="submit-course-unit-form"),
    path("delete-course-unit/<int:course_unit_id>/", views.delete_course_unit, name="delete-course-unit"),


### URLS for course_views.py
    # Enrolment
    path("enrolment-form/", views.get_enrolment_form, name="get-enrolment-form"),
    path("enrol/", views.enrol_in_course, name="enrol-in-course"),

    # Courses
    path("course/<int:course_id>/delete/", views.delete_course, name="delete-course"),
    path("course/<int:course_id>/reorder/", views.reorder_modal, name="reorder-modal"),
    path("reorder/<str:type>/<int:id>/<str:direction>/", views.reorder_item, name="reorder-item"),


### URLS for dmoj_views.py
    path("get-dmoj-form/<int:course_topic_id>/", views.get_dmoj_form, name="get-dmoj-form"),
    path("submit-dmoj-form/<int:course_topic_id>/", views.submit_dmoj_form, name="submit-dmoj-form"),
    path("activity/<int:activity_id>/edit-dmoj/", views.edit_dmoj_form, name="edit-dmoj-form"),
    path("exercise/<int:exercise_id>/update/", views.update_dmoj, name="update-dmoj"),


### URLS for home_views.py
    path("", views.home, name="home"),
    path("course/<int:course_id>/", views.course, name="course"),


### URLS for lesson_views.py
    path("topic/<course_topic_id>/lesson/create/", views.create_lesson, name="create-lesson"),
    path("topic/<int:course_topic_id>/lesson/<int:lesson_id>/edit/", views.edit_lesson, name="edit-lesson"),
    path("lessons/<lesson_id>/view/", views.view_lesson, name="view-lesson"),


### URLS for progress_views.py
    path("course/<int:course_id>/progress/", views.progress, name="progress"),


### URLS for quiz_views.py
    # Creation
    path("topic/<int:course_topic_id>/quiz-form/", views.get_quiz_form, name="get-quiz-form"),
    path("topic/<int:course_topic_id>/submit-quiz/", views.submit_quiz_form, name="submit-quiz-form"),

    # Taking
    path("course/<int:course_id>/activity/<int:activity_id>/start-quiz/", views.start_quiz, name="start-quiz"),
    path('quiz/<int:quiz_id>/activity/<int:activity_id>/take/', views.take_quiz, name='take-quiz'),

    # Results
    path("quiz/<int:ac_id>/results/", views.quiz_results, name="quiz-results"),


### URLS for unit_topic_management_views.py
    # Units
    path("manage-units/", views.manage_units, name="manage-units"),
    path("get-unit-form/", views.get_unit_form, name="get-unit-form"),
    path("submit-unit-form-manage/", views.submit_unit_form_manage, name="submit-unit-form-manage"),
    path("units/delete-selected/", views.delete_selected_units, name="delete-selected-units"),

    # Topics
    path("manage-topics/", views.manage_topics, name="manage-topics"),
    path("get-topic-form/", views.get_topic_form, name="get-topic-form"),
    path("submit-topic-form/", views.submit_topic_form, name="submit-topic-form"),
    path("topics/delete-selected/", views.delete_selected_topics, name="delete-selected-topics"),


### URLS for upload_questions_views.py
    # multiple choice questions
    path("questions/multiple-choice/", views.mc_questions, name="mc-questions"),
    path("questions/multiple-choice/upload/", views.upload_mc_questions, name="upload-mc-questions"),
    path("mc-question/<int:question_id>/edit/", views.edit_mc_question, name="edit-mc-question"),
    path("questions/multiple-choice/delete-selected/", views.delete_selected_mc_questions, name="delete-selected-mc-questions"),

    # tracing questions
    path("questions/tracing/", views.tracing_questions, name="tracing-questions"),
    path("questions/tracing/upload/", views.upload_tracing_questions, name="upload-tracing-questions"),
    path("tracing-question/<int:question_id>/edit/", views.edit_tracing_question, name="edit-tracing-question"),
    path("questions/tracing-choice/delete-selected/", views.delete_selected_tracing_questions, name="delete-selected-tracing-questions"),

### URLS for user_views.py
    path("login/", views.login_user, name="login"),
    path("register/", views.register_user, name="register-user"),
    path("logout/", views.logout_user, name = "logout"),
    path("update-theme/", views.update_theme, name="update-theme"),
    
    



    
    
    

    

    # quiz views
    #path("topic/<int:topic_id>/create-quiz/", views.create_quiz, name="create-quiz"),    

    # dmoj exercise views
    path("course/<int:course_id>/refresh_dmoj/", views.refresh_dmoj_progress, name="refresh-dmoj-progress"),
    
]