from django.contrib import admin
from .models import (
    Module,
    Questions
)

admin.site.register(Module)
admin.site.register(Questions)
