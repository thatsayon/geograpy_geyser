from django.urls import path

from module.views import (
    CreateModuleView,
    DeleteModuleView,
)
urlpatterns = [
    path('modules/', CreateModuleView.as_view(), name='Modules'),
    path('modules/<uuid:id>/delete/', DeleteModuleView.as_view(), name='delete_module'),

]
