import django_tables2 as tables
from ipam.models import IPAddress
from netbox.tables import NetBoxTable
from django.utils.translation import gettext_lazy as _

from gestion_impacts.custom import CustomActionsColumn


class ImpactTable(NetBoxTable):
    ip_address = tables.Column(accessor='ip_address', verbose_name=_('IP Address'), linkify=True)
    vrf_name = tables.Column(accessor='vrf_name', verbose_name='VRF')
    device_name = tables.Column(accessor='device_name', verbose_name='Device')
    vm_name = tables.Column(accessor='vm_name', verbose_name='VM')
    assigned_to = tables.Column(accessor='assigned_to', verbose_name=_('name'))
    impact = tables.Column(accessor='impact', verbose_name='Impact')
    redundancy = tables.Column(accessor='redundancy', verbose_name=_('Redundancy'))

    # Use the custom actions column
    actions = CustomActionsColumn()

    class Meta:
        model = IPAddress
        fields = ('ip_address', 'vrf_name', 'device_name', 'vm_name', 'assigned_to', 'impact', 'redundancy', 'actions')
        attrs = {
            'class': 'table table-striped table-bordered'
        }

    @property
    def htmx_url(self):
        return "/plugins/gestion_impacts/impacts/"
