from netbox.api.viewsets import NetBoxModelViewSet

from gestion_impacts.api.serializers import ImpactSerializer
from gestion_impacts.models import Impact


class ImpactViewSet(NetBoxModelViewSet):
    queryset = Impact.objects.all()
    serializer_class = ImpactSerializer
