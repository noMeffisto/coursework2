from rest_framework import serializers
from django.contrib.auth.models import User
from .models import (
    VehicleType, BodyType, Vehicle, Driver, Client,
    CargoType, Service, Order, Review
)

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'first_name', 'last_name', 'email')

class VehicleTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = VehicleType
        fields = '__all__'

class BodyTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = BodyType
        fields = '__all__'

class VehicleSerializer(serializers.ModelSerializer):
    vehicle_type = VehicleTypeSerializer(read_only=True)
    body_type = BodyTypeSerializer(read_only=True)
    
    class Meta:
        model = Vehicle
        fields = '__all__'

class DriverSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    vehicle = VehicleSerializer(read_only=True)
    
    class Meta:
        model = Driver
        fields = '__all__'

class ClientSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = Client
        fields = '__all__'

class CargoTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = CargoType
        fields = '__all__'

class ServiceSerializer(serializers.ModelSerializer):
    vehicle_type = VehicleTypeSerializer(read_only=True)
    
    class Meta:
        model = Service
        fields = '__all__'

class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = '__all__'

class OrderSerializer(serializers.ModelSerializer):
    client = ClientSerializer(read_only=True)
    service = ServiceSerializer(read_only=True)
    driver = DriverSerializer(read_only=True)
    cargo_type = CargoTypeSerializer(read_only=True)
    review = ReviewSerializer(read_only=True)
    
    class Meta:
        model = Order
        fields = '__all__'
        read_only_fields = ('total_price', 'status', 'created_at', 'updated_at') 