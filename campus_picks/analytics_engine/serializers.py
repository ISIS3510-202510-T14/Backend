from rest_framework import serializers
from .models import ApiLog

class ApiLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = ApiLog
        fields = '__all__'