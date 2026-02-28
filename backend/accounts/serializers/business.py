from rest_framework import serializers
from accounts.models import Business
import secrets


class BusinessSerializer(serializers.ModelSerializer):
    user_count = serializers.IntegerField(read_only=True, source='user_count')
    admin_count = serializers.IntegerField(read_only=True, source='admin_count')
    can_add_user = serializers.BooleanField(read_only=True, source='can_add_user')
    can_add_admin = serializers.BooleanField(read_only=True, source='can_add_admin')

    class Meta:
        model = Business
        fields = [
            'id',
            'name',
            'api_key',
            'max_users',
            'max_admins',
            'user_count',
            'admin_count',
            'can_add_user',
            'can_add_admin',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'api_key',
            'max_users',
            'max_admins',
            'created_at',
            'updated_at',
        ]


class BusinessUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Business
        fields = ['name']


# api key can only be changed through here. 
# It requires explicit 'confirm: true' in the request to prevent accidental key regeneration, which would break live widget embeds using the old key
class RegenerateApiKeySerializer(serializers.Serializer):
    confirm = serializers.BooleanField()

    def validate_confirm(self, value):
        if not value:
            raise serializers.ValidationError('You must confirm to regenerate the API key. ' 'This will invalidate your existing key immediately.')
        
        return value

    def update(self, instance, validated_data):
        instance.api_key = secrets.token_urlsafe(48)
        instance.save()
        
        return instance