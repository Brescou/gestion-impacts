from netbox.filtersets import NetBoxModelFilterSet

from .models import Impact


class ImpactFilterSet(NetBoxModelFilterSet):
    class Meta:
        model = Impact
        fields = ('name', 'redundancy', 'device', 'ip_address', 'vm')
