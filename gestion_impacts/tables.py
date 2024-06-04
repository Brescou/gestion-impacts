import django_tables2 as tables
from ipam.models import IPAddress
from netbox.tables import NetBoxTable

from gestion_impacts.models import Impact


class ImpactTable(NetBoxTable):
    ip_address = tables.Column(accessor='ip_address', verbose_name='IP Address')
    vrf_name = tables.Column(accessor='vrf_name', verbose_name='VRF Name')
    device_name = tables.Column(accessor='device_name', verbose_name='Device Name')
    vm_name = tables.Column(accessor='vm_name', verbose_name='VM Name')
    assigned_to = tables.Column(accessor='assigned_to', verbose_name='Assigned To')
    impact = tables.Column(accessor='impact', verbose_name='Impact')
    redundancy = tables.Column(accessor='redundancy', verbose_name='Redundancy')

    class Meta:
        model = IPAddress
        fields = ('ip_address', 'vrf_name', 'device_name', 'vm_name', 'assigned_to', 'impact', 'redundancy')
        attrs = {
            'class': 'table table-striped table-bordered'
        }