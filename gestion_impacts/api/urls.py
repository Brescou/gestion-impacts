from netbox.api.routers import NetBoxRouter

from .views import ImpactViewSet

app_name = 'gestion_impacts'

router = NetBoxRouter()
router.register('impact', ImpactViewSet)

urlpatterns = router.urls
