from django.db import models
from django.db.models import Q
from django_filters import filters
from ipam.models import IPAddress, VRF
from netbox.filtersets import NetBoxModelFilterSet


class ImpactFilterSet(NetBoxModelFilterSet):
    vrf = filters.CharFilter(method='filter_vrf_name', label='VRF Name')

    class Meta:
        model = IPAddress
        fields = ['address', 'vrf']
        filter_overrides = {
            models.GenericIPAddressField: {
                'filter_class': filters.CharFilter,
            },
            IPAddress._meta.get_field('address').__class__: {
                'filter_class': filters.CharFilter,
            },
        }

    def search(self, queryset, name, value):
        """
        Override this method to apply a general-purpose search logic.
        """
        return queryset.filter(
            Q(ip_address__icontains=value) |
            Q(impact__icontains=value) |
            Q(assigned_to__icontains=value)
        )

    @staticmethod
    def filter_vrf_name(queryset, name, value):
        return queryset.filter(vrf_name__icontains=VRF.objects.filter(id=value).values('name')[:1])
