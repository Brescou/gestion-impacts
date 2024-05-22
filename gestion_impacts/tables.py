import django_tables2 as tables
from netbox.tables import NetBoxTable

from .models import Impact


class ImpactTable(NetBoxTable):
    name = tables.Column()
    redundacy = tables.BooleanColumn()
    device = tables.Column(
        linkify=True
    )
    ip_address = tables.Column(
        linkify=True
    )
    vm = tables.Column(
        linkify=True
    )

    class Meta(NetBoxTable.Meta):
        model = Impact
        fields = ('pk', 'id', 'name', 'redundacy', 'device', 'ip_address', 'vm')
        default_columns = ('pk', 'name', 'redundacy', 'device', 'ip_address', 'vm')
