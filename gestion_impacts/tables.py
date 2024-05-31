import django_tables2 as tables
from django_tables2.utils import Accessor
from netbox.tables import NetBoxTable

from .models import Impact


class ImpactTable(NetBoxTable):
    ip_address = tables.Column(accessor=Accessor("ipaddress__address"), verbose_name='Adresse IP', linkify=True)
    vrf = tables.Column(accessor=Accessor('vrf__name'), verbose_name='VRF', linkify=True)
    role = tables.Column(accessor='ipaddress__role', verbose_name='Rôle', linkify=True)
    impact = tables.Column(accessor='impact', verbose_name='Impact')
    assigned_to = tables.Column(accessor='assigned_to', verbose_name='Attribuer',linkify=True)
    redundancy = tables.Column(verbose_name='Redondance')

    class Meta(NetBoxTable.Meta):
        model = Impact
        fields = ('ip_address', 'vrf', 'role', 'assigned_to', 'impact', 'assigned_to', 'redundancy')
        default_columns = ('ip_address', 'vrf', 'role', 'assigned_to', 'impact', 'assigned_to', 'redundancy')
