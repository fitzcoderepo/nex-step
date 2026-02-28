from django.db import transaction
from django.utils import timezone
from rest_framework import serializers
from accounts.models import Business, User, Invite
import secrets


class BusinessRegistrationSerializer(serializers.Serializer):
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