from django.urls import path
from .views import (
    CreateModuleView,
    CreateQuestionView,
    CustomTimeView,
    QuestionQuantityView,
)

urlpatterns = [
    path('module-list/', CreateModuleView.as_view(), name='Module'),
    path('question/', CreateQuestionView.as_view(), name='Question'),
    path('custom-time/', CustomTimeView.as_view(), name='Custom Time'),
    path('question-quantity/', QuestionQuantityView.as_view(), name='Question Quality'),
]
