from netbox.api.serializers import NetBoxModelSerializer

from gestion_impacts.models import Impact


class ImpactSerializer(NetBoxModelSerializer):
    class Meta:
        model = Impact
        fields = ('id', 'impact', 'redundancy', 'ip_address', 'vrf')
