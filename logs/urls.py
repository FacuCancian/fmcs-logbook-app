from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'drivers', views.DriverViewSet)
router.register(r'logdays', views.LogDayViewSet)
router.register(r'segments', views.DutySegmentViewSet)

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('logs.urls')),
]