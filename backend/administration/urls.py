from django.urls import path

from module.views import (
    CreateModuleView,
    DeleteModuleView,
    CreateQuestionView,
)
urlpatterns = [
    path('modules/', CreateModuleView.as_view(), name='Modules'),
    path('modules/<uuid:id>/delete/', DeleteModuleView.as_view(), name='Delete Module'),
    path('questions/', CreateQuestionView.as_view(), name='Questions'),
]
