from rest_framework import serializers
from .models import Customer
from .crypto import decrypt

class CustomerSerializer(serializers.ModelSerializer):
    email = serializers.SerializerMethodField()
    phone = serializers.SerializerMethodField()

    class Meta:
        model = Customer
        fields = ['id', 'name', 'company', 'email', 'phone']

    def get_email(self, obj):
        return decrypt(obj.email)

    def get_phone(self, obj):
        return decrypt(obj.phone)