from django.contrib import admin
from .models import (
    Module,
    Questions,
    OptionModulesPair
)

admin.site.register(Module)
admin.site.register(Questions)
admin.site.register(OptionModulesPair)
