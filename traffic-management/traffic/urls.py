from django.urls import path, include

from rest_framework.routers import DefaultRouter

from .views import (
    JunctionViewSet,
    SensorEventViewSet,
    ControllerEventViewSet,
    ControllerCommandViewSet,
)

router = DefaultRouter(trailing_slash=False)

router.register(r"junctions", JunctionViewSet, basename="junction")

router.register(r"sensor-events", SensorEventViewSet, basename="sensor-event")

router.register(
    r"controller-events", ControllerEventViewSet, basename="controller-event"
)

router.register(
    r"controller-commands", ControllerCommandViewSet, basename="controller-command"
)

from .views import run_migrations

def db_info(request):
    try:
        from django.conf import settings
        return JsonResponse({'engine': settings.DATABASES['default']['ENGINE']})
    except Exception as e:
        import traceback
        return JsonResponse({'error': str(e), 'trace': traceback.format_exc()}, status=500)

urlpatterns = [
    path("migrate/", run_migrations),
    path("db-info/", db_info),
    path("", include(router.urls)),
]
