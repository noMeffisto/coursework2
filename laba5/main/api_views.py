import logging
from rest_framework import viewsets, permissions, filters, authentication
from django.db.models import Avg, Count, Sum
from django.utils import timezone
from .models import (
    VehicleType, BodyType, Vehicle, Driver, CargoType,
    Service, Client, Order
)
from .serializers import (
    VehicleTypeSerializer, BodyTypeSerializer, VehicleSerializer,
    DriverSerializer, CargoTypeSerializer, ServiceSerializer,
    ClientSerializer, OrderSerializer
)
from rest_framework.exceptions import NotAuthenticated, PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response

logger = logging.getLogger(__name__)

class CustomAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        if not request.user.is_authenticated:
            return None
        return (request.user, None)

class CustomIsAuthenticated(permissions.BasePermission):
    def has_permission(self, request, view):
        if not bool(request.user and request.user.is_authenticated):
            from rest_framework.exceptions import NotAuthenticated
            raise NotAuthenticated()
        return True

def custom_exception_handler(exc, context):
    if isinstance(exc, PermissionDenied) and not context['request'].user.is_authenticated:
        exc = NotAuthenticated()
    from rest_framework.views import exception_handler
    return exception_handler(exc, context)

class BaseViewSet(viewsets.ModelViewSet):
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    authentication_classes = [authentication.SessionAuthentication, authentication.BasicAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [permissions.IsAdminUser]
        return [permission() for permission in permission_classes]

class VehicleTypeViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = VehicleType.objects.all()
    serializer_class = VehicleTypeSerializer
    permission_classes = [IsAuthenticated]

class BodyTypeViewSet(BaseViewSet):
    queryset = BodyType.objects.all()
    serializer_class = BodyTypeSerializer
    search_fields = ['name', 'description']
    ordering_fields = ['name']

class VehicleViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Vehicle.objects.all()
    serializer_class = VehicleSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Vehicle.objects.all()
        vehicle_type = self.request.query_params.get('vehicle_type', None)
        body_type = self.request.query_params.get('body_type', None)
        available = self.request.query_params.get('available', None)

        if vehicle_type:
            queryset = queryset.filter(vehicle_type_id=vehicle_type)
        if body_type:
            queryset = queryset.filter(body_type_id=body_type)
        if available:
            queryset = queryset.filter(is_available=True)

        return queryset

class DriverViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Driver.objects.all()
    serializer_class = DriverSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Driver.objects.all()
        experience = self.request.query_params.get('experience', None)

        if experience:
            queryset = queryset.filter(experience__gte=experience)

        return queryset

class CargoTypeViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = CargoType.objects.all()
    serializer_class = CargoTypeSerializer
    permission_classes = [IsAuthenticated]

class ServiceViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Service.objects.filter(is_active=True)
    serializer_class = ServiceSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Service.objects.filter(is_active=True)
        min_price = self.request.query_params.get('min_price', None)
        max_price = self.request.query_params.get('max_price', None)
        vehicle_type = self.request.query_params.get('vehicle_type', None)

        if min_price:
            queryset = queryset.filter(base_price__gte=min_price)
        if max_price:
            queryset = queryset.filter(base_price__lte=max_price)
        if vehicle_type:
            queryset = queryset.filter(vehicle_type_id=vehicle_type)

        return queryset

class ClientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Client.objects.all()
    serializer_class = ClientSerializer
    permission_classes = [IsAuthenticated]

class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if hasattr(user, 'driver'):
            return Order.objects.filter(driver=user.driver)
        elif hasattr(user, 'client'):
            return Order.objects.filter(client=user.client)
        return Order.objects.none()

    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        order = self.get_object()
        status = request.data.get('status')
        
        if status and status in dict(Order.STATUS_CHOICES):
            order.status = status
            order.save()
            return Response({'status': 'success'})
        return Response({'status': 'error', 'message': 'Invalid status'}, status=400)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        order = self.get_object()
        if order.status == 'pending':
            order.status = 'cancelled'
            order.save()
            return Response({'status': 'success'})
        return Response(
            {'status': 'error', 'message': 'Order can only be cancelled when pending'},
            status=400
        )

    def perform_create(self, serializer):
        if serializer.validated_data['delivery_date'] <= serializer.validated_data['pickup_date']:
            from rest_framework.exceptions import ValidationError
            raise ValidationError({
                'delivery_date': ['Дата доставки должна быть позже даты загрузки']
            })
        serializer.save()

    def perform_update(self, serializer):
        logger.info(f"Updating order {serializer.instance.id} by user {self.request.user}")
        serializer.save()

    def perform_destroy(self, instance):
        logger.info(f"Deleting order {instance.id} by user {self.request.user}")
        instance.delete() 