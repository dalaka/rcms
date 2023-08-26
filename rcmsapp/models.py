from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.timezone import now

ROLE=(
    ('admin', 'Admin'),
    ('staff', 'Staff'),
    ('customer', 'Customer'),
)
class UserManager(BaseUserManager):
    """Define a model manager for User model with no username field."""

    use_in_migrations = True

    def _create_user(self, username, password, **extra_fields):
        """Create and save a User with the given email and password."""
        if not username:
            raise ValueError('The given username must be set')
        user = self.model(username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, username, password=None, **extra_fields):
        """Creates and saves a new User"""
        user = self.model(username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, password, **extra_fields):
        """Create and save a SuperUser with the given email and password."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        # extra_fields.setdefault('groups_id', 1)
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        return self._create_user(username, password, **extra_fields)



class User(AbstractUser):


    """Custom user model that supports using email instead of username"""
    email = models.EmailField(max_length=255)
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    modified_at = models.DateTimeField(default=now)
    created_at = models.DateTimeField(default=now)
    role = models.CharField(choices=ROLE, default='customer')
    objects = UserManager()


class Company(models.Model):
    tin = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    address = models.CharField(max_length=255)
    created_at = models.DateTimeField(default=now)

    def __str__(self):
        return self.name

class Transaction(models.Model):

    tax_item = models.CharField(max_length=255, blank=True)
    month = models.CharField(max_length=255, blank=True)
    year = models.CharField(max_length=255, blank=True)
    taxpayer_name = models.CharField(max_length=255, blank=True)
    tin = models.CharField(max_length=255, blank=True)
    amount_paid = models.FloatField(default=0)

    def __str__(self):
        return self.month+'-'+self.year
class Item(models.Model):
    name = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return self.name

class Report(models.Model):
    year = models.CharField(max_length=255, blank=True)
    start = models.CharField(max_length=255, blank=True)
    end  = models.CharField(max_length=255, blank=True)
    item = models.ForeignKey(Item, on_delete=models.PROTECT,related_name="report_item")
    created_at = models.DateTimeField(default=now)
    total_compiled_organisaction = models.IntegerField(default=0)
    total_defaulted_organisaction = models.IntegerField(default=0)
    total_liability = models.FloatField(default=0)
    data = models.JSONField()

    def __str__(self):
        return self.start +"-"+ self.end



class Config(models.Model):
    name=models.CharField(max_length=50)
    interest = models.FloatField(default=0)
    penalty = models.FloatField(default=0)

    def __str__(self):
        return self.name





