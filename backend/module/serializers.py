from rest_framework import serializers
from .models import (
    Module,
    Questions,
    CustomTime,
    QuestionQuantity,
    OptionModulesPair
)

class ModuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Module
        fields = (
            'id',
            'module_name'
        )

class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Questions
        fields = (
            'id',
            'module',
            'question_text',
            'option1',
            'option2',
            'option3',
            'option4',
            'order'
        )

class CustomTimeSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomTime
        fields = (
            'id',
            'duration'
        )

class QuestionQuantitySerializer(serializers.ModelSerializer):
    class Meta:
        model = QuestionQuantity
        fields = (
            'id',
            'quantity'
        )

class OptionModulesPairSerializer(serializers.ModelSerializer):
    class Meta:
        model = OptionModulesPair
        fields = (
            'id',
            'module_a',
            'module_b',
            'pair_number'
        )

    def validate(self, data):
        module_a = data.get("module_a")
        module_b = data.get("module_b")
        pair_number = data.get("pair_number")

        # 1️⃣ Same module check
        if module_a == module_b:
            raise serializers.ValidationError(
                {"module_b": "A module cannot be paired with itself."}
            )

        # 2️⃣ Reverse duplicate check
        if OptionModulesPair.objects.filter(
            module_a=module_b, module_b=module_a
        ).exists():
            raise serializers.ValidationError(
                "This module pair already exists in reverse order."
            )

        # 3️⃣ Max 3 pairs total
        if OptionModulesPair.objects.count() >= 3:
            raise serializers.ValidationError(
                "You can only have up to 3 OptionModulesPair objects."
            )

        # 4️⃣ pair_number validation
        if pair_number not in [1, 2, 3]:
            raise serializers.ValidationError(
                {"pair_number": "pair_number must be 1, 2, or 3."}
            )

        return data
