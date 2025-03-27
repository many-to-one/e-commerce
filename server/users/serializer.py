from django.contrib.auth.password_validation import validate_password
from django.db import IntegrityError
from django.core.exceptions import ValidationError as DjangoValidationError

from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework.exceptions import ValidationError

from users.models import User, Profile


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
    )
    password2 = serializers.CharField(
        write_only=True,
        required=True,
    )

    class Meta:
        model = User
        fields = ['full_name', 'email', 'phone', 'password', 'password2']

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs

    def create(self, validated_data):

        try:
            user = User.objects.create(
                full_name=validated_data['full_name'],
                email=validated_data['email'],
                phone=validated_data['phone'],
            )

            email_user, mobile = user.email.split("@")
            user.username = email_user
            # # Validate the password
            # try:
            #     validate_password(validated_data['password'], user)
            # except DjangoValidationError as e:
            #     user.delete()
            #     raise ValidationError({"password": e.messages})
            user.set_password(validated_data['password'])
            user.save()

            return user
        except IntegrityError:
            raise ValidationError({"username": f"{validated_data['full_name']} already exists"})


class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        token['full_name'] = user.full_name
        token['email'] = user.email
        token['username'] = user.username
        try:
            token['vendor_id'] = user.vendor.id
        except:
            token['vendor_id'] = 0

        return token


class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = '__all__'


class EmailSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ['email']


class PasswordChangeSerializer(serializers.Serializer):
    uidb64 = serializers.IntegerField()
    otp = serializers.CharField(max_length=1000)
    password = serializers.CharField(write_only=True, min_length=8)


class ProfileSerializer(serializers.ModelSerializer):

    class Meta:
        model = Profile
        fields = '__all__'

    def to_representation(self, instance):
        response =  super().to_representation(instance)
        response['user'] = UserSerializer(instance.user).data
        return response
    