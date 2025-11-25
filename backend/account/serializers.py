from rest_framework import serializers
from module.models import OptionModulesPair, Module
from .models import OptionalModule

class ModuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Module
        fields = ['id', 'module_name']

class OptionModulesPairSerializer(serializers.ModelSerializer):
    modules = serializers.SerializerMethodField()
    selected_module = serializers.SerializerMethodField()

    class Meta:
        model = OptionModulesPair
        fields = ['pair_number', 'modules', 'selected_module']

    def get_modules(self, obj):
        return ModuleSerializer([obj.module_a, obj.module_b], many=True).data

    def get_selected_module(self, obj):
        user = self.context['request'].user
        data = OptionalModule.objects.filter(
            student=user,
            pair_number=obj.pair_number
        ).first()
        return str(data.selected_module.id) if data else None

