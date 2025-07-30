DEFAULT_COURSE_WEIGHTINGS = {
    "lesson": 1,
    "quiztemplate_multiple_choice": 1,
    "quiztemplate_tracing": 1,
    "quiztemplate_fill_in_the_blank": 1,
    "codequestion": 1,
    "dmojexercise": 1,
}

ACTIVITY_TYPE_DISPLAY = {
        "lesson": "Lesson",
        "dmojexercise": "DMOJ Exercise",
        "codequestion": "Code Question",
        "quiztemplate_multiple_choice": "Multiple Choice",
        "quiztemplate_tracing": "Tracing",
        "quiztemplate": "Quiz Template",
        "quiztemplate_fill_in_the_blank": "Fill in the Blank",
    }

# models.py: Used by the teacher to create a quiz template
QUESTION_TYPE_CHOICES = [
    ("multiple_choice", "Multiple Choice"),
    ("tracing", "Tracing"),
    ("fill_in_the_blank", "Fill in the Blank"),
    ("stdin", "Standard Input"),
    ("exec", "Python Exec Block"),  # for function/class-based testing
]

DEFAULT_QUIZ_QUESTION_COUNT = 5
QUIZ_QUESTION_COUNT_OPTIONS = [1, 2, 5, 10, 15, 20]