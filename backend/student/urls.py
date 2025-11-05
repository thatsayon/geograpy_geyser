from django.urls import path
from module.views import (
    CreateModuleView,
    CustomTimeView,
)
from .views import (
    QuizTestView,
)

urlpatterns = [
    path('module-list/', CreateModuleView.as_view()),
    path('time-list/', CustomTimeView.as_view()),
    path('quiz-test/', QuizTestView.as_view()),
]
