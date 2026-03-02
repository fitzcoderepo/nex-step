from django.utils import timezone
from datetime import timedelta
from rest_framework import serializers
from accounts.models import User, Invite


class UserSerializer(serializers.ModelSerializer):
    """
    Read only serializer for displaying user details.

    Used for listing and retrieving user information within a business.
    Email and id are always read only regardless of context.

    Args:
        instance (User): The User instance to serialize.

    Returns:
        dict: Serialized user data including id, email, full_name,
              role, is_active, and timestamps.
    """

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


class UpdateUserRoleSerializer(serializers.ModelSerializer):
    """
    Handles updating a user's role within a business.

    Enforces role change restrictions — the owner role cannot be
    assigned or changed, admins cannot change other admins' roles,
    and the admin cap is respected when promoting a user to admin.

    Args:
        role (str): The new role to assign. Choices are admin or author.

    Raises:
        serializers.ValidationError: If attempting to change or assign the owner role.
        serializers.ValidationError: If the business has reached its admin cap.
        serializers.ValidationError: If an admin attempts to change another admin's role.

    Returns:
        User: The updated User instance.
    """

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


class DeactivateUserSerializer(serializers.Serializer):
    """
    Handles user deactivation within a business.

    Enforces deactivation restrictions — users cannot deactivate
    themselves, the owner cannot be deactivated, and admins cannot
    deactivate other admins.

    Args:
        confirm (bool): Must be True to proceed. Prevents accidental deactivation.

    Raises:
        serializers.ValidationError: If confirm is False or not provided.
        serializers.ValidationError: If the user is attempting to deactivate themselves.
        serializers.ValidationError: If attempting to deactivate the owner.
        serializers.ValidationError: If an admin attempts to deactivate another admin.

    Returns:
        None
    """

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
    """
    Read only serializer for displaying invite details.

    Used for listing and retrieving existing invites within a business.

    Args:
        instance (Invite): The Invite instance to serialize.

    Returns:
        dict: Serialized invite data including id, email, role,
              accepted status, expiry, and created timestamp.
    """

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



class CreateInviteSerializer(serializers.ModelSerializer):
    """
    Handles creating a new user invite for a business.

    Validates that the business has capacity for a new user, that no
    active invite already exists for the email, and that role assignment
    rules are respected. Sets the invite expiry to 7 days from creation.

    Args:
        email (str): The email address to send the invite to.
        role (str): The role to assign the invited user. Choices are admin or author.

    Raises:
        serializers.ValidationError: If the email already belongs to a user in the business.
        serializers.ValidationError: If an active invite for the email already exists.
        serializers.ValidationError: If the business has reached its maximum user count.
        serializers.ValidationError: If the business has reached its maximum admin count.
        serializers.ValidationError: If an admin attempts to invite another admin.
        serializers.ValidationError: If the owner role is specified.

    Returns:
        Invite: The newly created Invite instance.
    """
    
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