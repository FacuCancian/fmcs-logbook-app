from rest_framework import viewsets, permissions
from .models import Driver, LogDay, DutySegment
from .serializers import DriverSerializer, LogDaySerializer, DutySegmentSerializer


class DriverViewSet(viewsets.ModelViewSet):
    queryset = Driver.objects.all()
    serializer_class = DriverSerializer
    permission_classes = [permissions.AllowAny]


class LogDayViewSet(viewsets.ModelViewSet):
    queryset = LogDay.objects.all()
    serializer_class = LogDaySerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        queryset = super().get_queryset()
        driver_id = self.request.query_params.get('driver_id', None)
        if driver_id:
            queryset = queryset.filter(driver_id=driver_id)
        return queryset


class DutySegmentViewSet(viewsets.ModelViewSet):
    queryset = DutySegment.objects.all()
    serializer_class = DutySegmentSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        queryset = super().get_queryset()
        log_day_id = self.request.query_params.get('log_day_id', None)
        if log_day_id:
            queryset = queryset.filter(log_day_id=log_day_id)
        return queryset