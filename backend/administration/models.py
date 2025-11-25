from django.db import models
from module.models import Module
import uuid

class SynopticModule(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    modules = models.ManyToManyField(Module, related_name='synoptic_module')
    created_at = models.DateTimeField(auto_now_add=True)

    def get_main_module(self):
        # Always return the module named "synoptic"
        return Module.objects.get_or_create(module_name="synoptic")[0]

    def __str__(self):
        return "Synoptic Module"
