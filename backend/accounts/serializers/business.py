from rest_framework import serializers
from accounts.models import Business
import secrets


class BusinessSerializer(serializers.ModelSerializer):
    """
    Read only serializer for displaying full business details.

    Exposes business information including computed properties for
    user and admin counts and capacity checks. Used for display
    purposes only — no writing is permitted through this serializer.

    Args:
        instance (Business): The Business instance to serialize.

    Returns:
        dict: Serialized business data including id, name, api_key,
              capacity fields, and timestamps.
    """

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
    """
    Handles updating the business name.

    Only exposes the name field for updating. All other business
    fields are managed through dedicated endpoints or set automatically.

    Args:
        name (str): The new name for the business.

    Returns:
        Business: The updated Business instance.
    """
    class Meta:
        model = Business
        fields = ['name']


class RegenerateApiKeySerializer(serializers.Serializer):
    """
    Handles API key rotation for a business with a grace period.

    When confirmed, the current API key is moved to old_api_key and a new
    key is generated. The old key remains valid for the duration of the
    grace period, allowing the business owner time to update their embed
    code without disrupting live widget deployments.

    Args:
        confirm (bool): Must be True to proceed. Prevents accidental key rotation.
        grace_period_hours (int): How long the old key remains valid after rotation.
                                Defaults to 48 hours, maximum 168 hours (7 days).

    Raises:
        serializers.ValidationError: If confirm is False or not provided.
        serializers.ValidationError: If grace_period_hours is outside the range of 1-168.

    Returns:
        Business: The updated Business instance with the new api_key set
                and the old key saved to old_api_key with an expiry timestamp.
    """
    confirm = serializers.BooleanField()
    grace_period_hours = serializers.IntegerField(default=48, min_value=1, max_value=168)

    def validate_confirm(self, value):
        if not value:
            raise serializers.ValidationError('You must confirm to regenerate the API key. ' 'This will invalidate your existing key after the grace period.')
        
        return value

    def update(self, instance, validated_data):
        from django.utils import timezone
        from datetime import timedelta

        grace_hours = validated_data.get('grace_period_hours', 48)
        instance.old_api_key = instance.api_key
        instance.old_api_key_expires_at = timezone.now() + timedelta(hours=grace_hours)
        instance.api_key = secrets.token_urlsafe(48)
        instance.save()
        
        return instance