from django.db import models
from django.contrib.auth import get_user_model
from module.models import Module
import uuid

User = get_user_model()

class OptionalModule(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='optional_modules'
    )
    selected_module = models.ForeignKey(
        Module,
        on_delete=models.CASCADE
    )
    pair_number = models.PositiveIntegerField()

    class Meta:
        unique_together = ('student', 'pair_number')

    def __str__(self):
        return f"{self.student} → {self.selected_module} (Pair {self.pair_number})"
