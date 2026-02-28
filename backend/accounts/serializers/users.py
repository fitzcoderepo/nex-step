from django.utils import timezone
from datetime import timedelta
from rest_framework import serializers
from accounts.models import User, Invite


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id',
            'email',
            'full_name',
            'role',
            'is_active',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'email',
            'created_at',
            'updated_at',
        ]


# enforce owner role can never be assigned or changed by anyone, admins cannot change roles of other admins, admin cap is respected when promoting someone to admin
class UpdateUserRoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['role']

    def validate_role(self, value):
        user = self.instance
        requesting_user = self.context['request'].user

        if user.role == User.Roles.OWNER:
            raise serializers.ValidationError('The owner role cannot be changed.')

        if value == User.Roles.OWNER:
            raise serializers.ValidationError('The owner role cannot be assigned.')

        if value == User.Roles.ADMIN:
            business = user.business
            current_admin_count = business.admin_count
            if user.role != User.Roles.ADMIN and not business.can_add_admin:
                raise serializers.ValidationError(
                    f'This business has reached its maximum of {business.max_admins} admins.'
                )

        if requesting_user.role == User.Roles.ADMIN:
            if user.role == User.Roles.ADMIN and user != requesting_user:
                raise serializers.ValidationError(
                    'Admins cannot change the role of other admins.'
                )

        return value


# prevent self-deactivation, protect owner account, stops admins from deactivating each other
class DeactivateUserSerializer(serializers.Serializer):
    confirm = serializers.BooleanField()

    def validate_confirm(self, value):
        if not value:
            raise serializers.ValidationError('You must confirm to deactivate this user.')
        
        return value

    def validate(self, data):
        user = self.context['user']
        requesting_user = self.context['request'].user

        if user == requesting_user:
            raise serializers.ValidationError('You cannot deactivate your own account.')

        if user.role == User.Roles.OWNER:
            raise serializers.ValidationError('The owner account cannot be deactivated.')

        if requesting_user.role == User.Roles.ADMIN and user.role == User.Roles.ADMIN:
            raise serializers.ValidationError('Admins cannot deactivate other admins.')

        return data


class InviteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Invite
        fields = [
            'id',
            'email',
            'role',
            'accepted',
            'expires_at',
            'created_at',
        ]
        read_only_fields = [
            'id',
            'accepted',
            'expires_at',
            'created_at',
        ]


# check user and admin caps before creating invite, prevent duplicate invite to same email, stops admins from inviting other admins, owner invites admins
class CreateInviteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Invite
        fields = ['email', 'role']

    def validate_role(self, value):
        if value == User.Roles.OWNER:
            raise serializers.ValidationError('Cannot invite a user with the owner role.')
        
        return value

    def validate_email(self, value):
        email = value.lower()
        business = self.context['request'].user.business

        if User.objects.filter(email=email, business=business).exists():
            raise serializers.ValidationError('A user with this email already exists in your business')

        if Invite.objects.filter(email=email, business=business, accepted=False).exists():
            raise serializers.ValidationError('An active invite for this email already exists')

        return email

    def validate(self, data):
        business = self.context['request'].user.business
        requesting_user = self.context['request'].user

        if not business.can_add_user:
            raise serializers.ValidationError(f'This business has reached its maximum of {business.max_users} users')

        if data['role'] == User.Roles.ADMIN and not business.can_add_admin:
            raise serializers.ValidationError(f'This business has reached its maximum of {business.max_admins} admins')

        if requesting_user.role == User.Roles.ADMIN and data['role'] == User.Roles.ADMIN:
            raise serializers.ValidationError('Admins cannot invite other admins.')

        return data

    def create(self, validated_data):
        business = self.context['request'].user.business
        invited_by = self.context['request'].user
        expires_at = timezone.now() + timedelta(days=7)

        return Invite.objects.create(business=business, invited_by=invited_by, email=validated_data['email'], role=validated_data['role'], expires_at=expires_at)