from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from rcmsapp.models import User, Company, Transaction, Config, Item, Report

from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView

class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # Add custom claims
        token['role'] = user.role
        token['is_superuser'] = user.is_superuser


        return token
def createuser(data):
    password = data['password']
    user = User.objects.create(first_name=data['first_name'], last_name=data['last_name'],username=data['username'],
                                email=data['email'],role=data["role"], is_staff=False, is_active=True)
    user.set_password(password)
    user.save()
    return user
class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ('id','username', 'email', 'password', 'is_active','role','last_login','last_name', 'first_name','modified_at','created_at')
        extra_kwargs = {'last_login': {'read_only': True},'is_active': {'read_only': True}, 'password': {'write_only': True, 'min_length': 4}, 'modified_at': {'read_only': True}, 'created_at': {'read_only': True}}

class ChangePasswordSerializer(serializers.ModelSerializer):
    new_password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    confirm_password = serializers.CharField(write_only=True, required=True)
    old_password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ('old_password', 'new_password', 'confirm_password')

    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError({"detail": "Password fields didn't match."})

        return attrs

    def validate_old_password(self, value):
        user = self.context['request'].user
        print(value)
        if not user.check_password(value):
            raise serializers.ValidationError({"detail": "Old password is not correct"})
        return value

    def update(self, instance, validated_data):

        instance.set_password(validated_data['new_password'])
        instance.save()

        return instance

class CompanySerializer(serializers.ModelSerializer):

    class Meta:
        model = Company
        fields = ('id','name', 'tin', 'address')

    def create(self, validated_data):

        for i in validated_data:
            Company.objects.create(name=i["taxpayer_name"].upper(),tin=i["tin"], address=i["address"])
        return True


class TranxSerializer(serializers.ModelSerializer):

    class Meta:
        model = Transaction
        fields = ('id','tax_item', 'month', 'year','taxpayer_name','amount_paid','tin')

    def create(self, validated_data,year,month,item):

        for i in validated_data:
            res=Transaction.objects.create(tin=i["tin"],amount_paid=i["amount_paid"],taxpayer_name=i["taxpayer_name"].upper(),tax_item=item,month=month, year=year)
        return res


class ConfigSerializer(serializers.ModelSerializer):

    class Meta:
        model = Config
        fields = ('id', 'penalty', 'interest')

class ItemSerializer(serializers.ModelSerializer):

    class Meta:
        model = Item
        fields = ('id', 'name')


class ReportSerializer(serializers.ModelSerializer):

    class Meta:
        model = Report
        fields = ('id', 'start','end','item', 'created_at','total_compiled_organisaction','total_defaulted_organisaction','total_liability','data')
