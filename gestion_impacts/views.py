from dcim.models import Device
from django.db.models import F, Value, CharField, Q, OuterRef, Subquery
from django.db.models.fields.json import KeyTextTransform
from django.db.models.functions import Coalesce
from ipam.models import IPAddress
from netbox.views import generic
from virtualization.models import VirtualMachine

from .filtersets import ImpactFilterSet
from .forms import ImpactForm, ImpactBulkImportForm, ImpactBulkEditForm
from .models import Impact
from .tables import ImpactTable


class ImpactView(generic.ObjectView):
    queryset = Impact.objects.all()


class ImpactListView(generic.ObjectListView):
    device_name_subquery = Device.objects.filter(
        interfaces__ip_addresses=OuterRef('pk')
    ).values('name')[:1]

    vm_name_subquery = VirtualMachine.objects.filter(
        interfaces__ip_addresses=OuterRef('pk')
    ).values('name')[:1]

    impact_subquery = Impact.objects.filter(
        ip_address=OuterRef('pk')
    ).values('impact')[:1]

    redundancy_subquery = Impact.objects.filter(
        ip_address=OuterRef('pk')
    ).values('redundancy')[:1]

    queryset = IPAddress.objects.annotate(
        ip_address=F('address'),
        vrf_name=F('vrf__name'),
        device_name=Subquery(device_name_subquery, output_field=CharField()),
        vm_name=Subquery(vm_name_subquery, output_field=CharField()),
        assigned_to=Coalesce(
            Subquery(device_name_subquery, output_field=CharField()),
            Subquery(vm_name_subquery, output_field=CharField()),
            KeyTextTransform('nom_long', 'custom_field_data', output_field=CharField()),
            Value('Not Assigned', output_field=CharField())
        ),
        impact=Subquery(impact_subquery, output_field=CharField()),
        redundancy=Subquery(redundancy_subquery, output_field=CharField())
    ).select_related('vrf').filter(
        Q(assigned_object_type__model='interface', assigned_object_type__app_label='dcim') |
        Q(assigned_object_type__model='vminterface', assigned_object_type__app_label='virtualization') |
        Q(assigned_object_id__isnull=True)
    )

    table = ImpactTable
    template_name = 'gestion_impacts/impact_list.html'
    paginate_by = 25

    def get_queryset(self, request):
        return self.queryset




class ImpactEditView(generic.ObjectEditView):
    queryset = Impact.objects.all()
    form = ImpactForm


class ImpactDeleteView(generic.ObjectDeleteView):
    queryset = Impact.objects.all()


class ImpactBulkImportView(generic.BulkImportView):
    queryset = Impact.objects.all()
    model_form = ImpactBulkImportForm
    table = ImpactTable


class ImpactBulkEditView(generic.BulkEditView):
    queryset = Impact.objects.all()
    form = ImpactBulkEditForm
    table = ImpactTable
    filterset = ImpactFilterSet


class ImpactBulkDeleteView(generic.BulkDeleteView):
    queryset = Impact.objects.all()
    table = ImpactTable
