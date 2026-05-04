from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'drivers', views.DriverViewSet)
router.register(r'logdays', views.LogDayViewSet)
router.register(r'segments', views.DutySegmentViewSet)

urlpatterns = [
    path('', include(router.urls)),
]