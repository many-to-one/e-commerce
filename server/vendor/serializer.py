from django.contrib.auth.password_validation import validate_password
from django.db import IntegrityError
from django.core.exceptions import ValidationError as DjangoValidationError

from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework.exceptions import ValidationError

from vendor.models import Vendor

class VendorSerializer(serializers.ModelSerializer):

    class Meta:
        model = Vendor
        fields = [
            'name',
            'email',
            'address',
            'mobile',
            'nip',
            'description'
        ]