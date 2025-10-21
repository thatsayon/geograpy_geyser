from django.db import models
from django.utils.text import slugify
import uuid

class CustomTime(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        unique=True
    )
    duration = models.PositiveIntegerField(unique=True)

class QuestionQuantity(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        unique=True
    )
    quantity = models.PositiveIntegerField(unique=True)


class Module(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        unique=True
    )
    module_name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, blank=True, null=True)

    def __str__(self):
        return self.module_name

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.module_name)
            slug = base_slug
            counter = 1
            # ensure uniqueness
            while Module.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)


class Questions(models.Model):
    class AnswerChoice(models.TextChoices):
        OPTION_1 = 'option1', 'Option 1'
        OPTION_2 = 'option2', 'Option 2'
        OPTION_3 = 'option3', 'Option 3'
        OPTION_4 = 'option4', 'Option 4'

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        unique=True
    )
    module = models.ForeignKey(
        'Module',
        on_delete=models.CASCADE,
        related_name='questions'
    )
    question_text = models.CharField(max_length=255)
    option1 = models.CharField(max_length=255)
    option2 = models.CharField(max_length=255)
    option3 = models.CharField(max_length=255)
    option4 = models.CharField(max_length=255)
    correct_answer = models.CharField(
        max_length=7,
        choices=AnswerChoice.choices,
        help_text="The correct answer option"
    )
    order = models.PositiveIntegerField(
        blank=True, null=True,
        help_text="Display order within the module"
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['module', 'order'],
                name='unique_order_per_module'
            )
        ]

    def save(self, *args, **kwargs):
        # If order is not provided, increment based on last order in the same module
        if self.order is None:
            last_order = Questions.objects.filter(module=self.module).aggregate(
                models.Max('order')
            )['order__max']
            self.order = (last_order or 0) + 1
        super().save(*args, **kwargs)

    def __str__(self):
        return self.question_text[:50] + "..." if len(self.question_text) > 50 else self.question_text

    def get_options(self):
        return {
            'option1': self.option1,
            'option2': self.option2,
            'option3': self.option3,
            'option4': self.option4,
        }

    def get_correct_answer_text(self):
        return getattr(self, self.correct_answer, None)

    def is_correct(self, answer):
        return answer == self.correct_answer
