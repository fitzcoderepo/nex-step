from django.db import transaction
from django.utils import timezone
from rest_framework import serializers
from accounts.models import Business, User, Invite
import secrets


class BusinessRegistrationSerializer(serializers.Serializer):
    """
    Handles business and owner account creation in a single transaction.

    Creates a Business record followed by a User record with the owner role.
    Both operations are wrapped in an atomic transaction so if either fails
    neither record is created.

    Args:
        business_name (str): The name of the business being registered.
        full_name (str): The full name of the owner.
        email (str): The owner's email address, used for login.
        password (str): The owner's password, minimum 8 characters.
        confirm_password (str): Must match password.

    Raises:
        serializers.ValidationError: If the email is already in use.
        serializers.ValidationError: If password and confirm_password do not match.

    Returns:
        User: The newly created owner User instance.
    """
    
    business_name = serializers.CharField(max_length=255)
    full_name = serializers.CharField(max_length=255)
    email = serializers.EmailField()
    password = serializers.CharField(min_length=8, write_only=True)
    confirm_password = serializers.CharField(min_length=8, write_only=True)

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError('A user with this email already exists')
        
        return value.lower()

    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError({'confirm_password': 'Passwords do not match'})
        
        return data

    # should anything fail during registration, we roll back using transaction.atomic 
    @transaction.atomic 
    def create(self, validated_data):
        business = Business.objects.create(name=validated_data['business_name'])
        user = User.objects.create_user(email=validated_data['email'], password=validated_data['password'], full_name=validated_data['full_name'], business=business, role=User.Roles.OWNER)
        
        return user
    

class LoginSerializer(serializers.Serializer):
    """
    Validates user credentials and returns the authenticated user.

    Args:
        email (str): The user's email address.
        password (str): The user's password.

    Raises:
        serializers.ValidationError: If the email or password is incorrect.
        serializers.ValidationError: If the user's account is inactive.

    Returns:
        dict: Validated data containing the authenticated User instance under the 'user' key.
    """

    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)    

    def validate(self, data):
        from django.contrib.auth import authenticate
        user = authenticate(request=self.context.get('request'), email=data['email'].lower(), password=data['password'])

        if not user:
            raise serializers.ValidationError('Invalid email or password')
        if not user.is_active:
            raise serializers.ValidationError('This account has been deactivated')

        data['user'] = user
        return data
    

class InviteAcceptSerializer(serializers.Serializer):
    """
    Handles invite acceptance and new user account creation.

    Validates the invite token, checks it hasn't been accepted or expired,
    creates the new user account, and marks the invite as accepted.
    Both the user creation and invite update are wrapped in an atomic transaction.

    Args:
        token (UUID): The unique invite token from the invite link.
        full_name (str): The full name of the invited user.
        password (str): The new user's password, minimum 8 characters.
        confirm_password (str): Must match password.

    Raises:
        serializers.ValidationError: If the token is invalid or already accepted.
        serializers.ValidationError: If the invite has expired.
        serializers.ValidationError: If password and confirm_password do not match.

    Returns:
        User: The newly created User instance.
    """
    
    token = serializers.UUIDField()
    full_name = serializers.CharField(max_length=255)
    password = serializers.CharField(min_length=8, write_only=True)
    confirm_password = serializers.CharField(min_length=8, write_only=True)

    def validate_token(self, value):
        try:
            invite = Invite.objects.get(token=value, accepted=False)
        except Invite.DoesNotExist:
            raise serializers.ValidationError('Invalid or already accepted invite')
        if invite.expires_at < timezone.now():
            raise serializers.ValidationError('This invite has expired')
        
        self.context['invite'] = invite
        return value

    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError({'confirm_password': 'Passwords do not match'})
        
        return data
    
    # storing the invite on the context so the create method can access it without querying the DB again.
    @transaction.atomic
    def create(self, validated_data):
        invite = self.context['invite']
        user = User.objects.create_user(email=invite.email, password=validated_data['password'], full_name=validated_data['full_name'], business=invite.business, role=invite.role)
        invite.accepted = True
        invite.save()
        
        return user