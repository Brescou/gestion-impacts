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

    # Subquery to get the virtual machine name from VMInterface
    vm_name_subquery = VirtualMachine.objects.filter(
        interfaces__ip_addresses=OuterRef('pk')
    ).values('name')[:1]

    # Subquery to get the impact details
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
    ).select_related(
        'vrf',
    ).filter(
        Q(assigned_object_type__model='interface', assigned_object_type__app_label='dcim') |
        Q(assigned_object_type__model='vminterface', assigned_object_type__app_label='virtualization') |
        Q(assigned_object_id__isnull=True)
    )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['query'] = str(self.get_queryset().query)  # For debugging
        return context

    table = ImpactTable
    template_name = 'gestion_impacts/impact_list.html'


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

    # queryset = IPAddress.objects.annotate(
    #     cf_nom_long=ExpressionWrapper(
    #         Func(F('custom_field_data'), Value('nom_long'), function='jsonb_extract_path_text'),
    #         output_field=CharField()
    #     )
    # ).annotate(
    #     assigned_to=Case(
    #         When(
    #             assigned_object_type=ContentType.objects.get_for_model(Interface),
    #             then=Subquery(
    #                 Interface.objects.filter(pk=OuterRef('assigned_object_id')).values('device__name')[:1]
    #             )
    #         ),
    #         When(
    #             assigned_object_type=ContentType.objects.get_for_model(VMInterface),
    #             then=Subquery(
    #                 VMInterface.objects.filter(pk=OuterRef('assigned_object_id')).values('virtual_machine__name')[:1]
    #             )
    #         ),
    #         default=F('cf_nom_long'),
    #         output_field=CharField(),
    #     )
    # )
