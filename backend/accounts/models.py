from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin, User
import uuid
import secrets


class Business(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)

    api_key = models.CharField(max_length=64, unique=True, editable=False)
    old_api_key = models.CharField(max_length=64, null=True, blank=True, editable=False)
    old_api_key_expires_at = models.DateTimeField(null=True, blank=True)
    
    max_users = models.PositiveIntegerField(default=10)
    max_admins = models.PositiveIntegerField(default=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.api_key:
            self.api_key = secrets.token_urlsafe(48)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name
    
    # helpers for checking and enforcing cap rules, reduces logic rewrite every time a check is needed
    @property
    def owner(self):
        return self.users.filter(role=User.Roles.OWNER).first()
    @property
    def admin_count(self):
        return self.users.filter(role=User.Roles.ADMIN).count()
    @property
    def user_count(self):
        return self.users.count()
    
    def can_add_user(self):
        return self.user_count < self.max_users
    @property
    def can_add_admin(self):
        return self.admin_count < self.max_admins
    

class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email address is required')
        
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)
    

class User(AbstractBaseUser, PermissionsMixin):
    class Roles(models.TextChoices):
        OWNER = 'owner', 'Owner'
        ADMIN = 'admin', 'Admin'
        AUTHOR = 'author', 'Author'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # allowing null for superusers that aren't a part of a business, but platform level admins
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='users', null=True, blank=True)
    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=255)
    role = models.CharField(max_length=10, choices=Roles.choices, default=Roles.AUTHOR)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['full_name']

    def __str__(self):
        return f'{self.full_name} ({self.email})'

    # helpers for permission checking
    @property
    def can_publish(self):
        return self.role in [self.Roles.OWNER, self.Roles.ADMIN]
    @property
    def can_manage_users(self):
        return self.role in [self.Roles.OWNER, self.Roles.ADMIN]


class Invite(models.Model):
    class Roles(models.TextChoices):
        ADMIN = 'admin', 'Admin'
        AUTHOR = 'author', 'Author'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='invites')
    invited_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='sent_invites')
    email = models.EmailField()
    role = models.CharField(max_length=10, choices=Roles.choices, default=Roles.AUTHOR)
    token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    accepted = models.BooleanField(default=False)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('business', 'email') # used to prevent duplicate pending invites to same email within a business

    def __str__(self):
        return f'Invite for {self.email} to {self.business.name} as {self.role}'
