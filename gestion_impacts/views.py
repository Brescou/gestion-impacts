from core.models import ObjectType
from dcim.models import Device
from django.db.models import F, Value, CharField, Q, OuterRef, Subquery
from django.db.models.fields.json import KeyTextTransform
from django.db.models.functions import Coalesce
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from extras.models import ExportTemplate
from ipam.models import IPAddress
from netbox.views import generic
from netbox.views.generic.utils import get_prerequisite_model
from utilities.htmx import htmx_partial
from virtualization.models import VirtualMachine

from .filtersets import ImpactFilterSet
from .forms import ImpactForm, ImpactBulkImportForm, ImpactBulkEditForm, ImpactIpAddressFilterSetForm
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
    filterset = ImpactFilterSet
    filterset_form = ImpactIpAddressFilterSetForm

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return self.filterset(self.request.GET, queryset=queryset).qs

    def get(self, request):
        """
        GET request handler.

        Args:
            request: The current request
        """
        model = self.queryset.model
        object_type = ObjectType.objects.get_for_model(model)

        if self.filterset:
            self.queryset = self.filterset(request.GET, self.queryset, request=request).qs

        # Determine the available actions
        actions = self.get_permitted_actions(request.user)
        has_bulk_actions = any([a.startswith('bulk_') for a in actions])

        if 'export' in request.GET:

            # Export the current table view
            if request.GET['export'] == 'table':
                table = self.get_table(self.queryset, request, has_bulk_actions)
                columns = [name for name, _ in table.selected_columns]
                return self.export_table(table, columns)

            # Render an ExportTemplate
            elif request.GET['export']:
                template = get_object_or_404(ExportTemplate, object_types=object_type, name=request.GET['export'])
                return self.export_template(template, request)

            # Check for YAML export support on the model
            elif hasattr(model, 'to_yaml'):
                response = HttpResponse(self.export_yaml(), content_type='text/yaml')
                filename = 'netbox_{}.yaml'.format(self.queryset.model._meta.verbose_name_plural)
                response['Content-Disposition'] = 'attachment; filename="{}"'.format(filename)
                return response

            # Fall back to default table/YAML export
            else:
                table = self.get_table(self.queryset, request, has_bulk_actions)
                return self.export_table(table)

        # Render the objects table
        table = self.get_table(self.queryset, request, has_bulk_actions)

        # If this is an HTMX request, return only the rendered table HTML
        if htmx_partial(request):
            if not request.htmx.target:
                table.embedded = True
                # Hide selection checkboxes
                if 'pk' in table.base_columns:
                    table.columns.hide('pk')
            return render(request, 'htmx/table.html', {
                'table': table,
            })

        action_to_remove = ['bulk_import', 'add', 'import']
        for action in action_to_remove:
            if action in actions:
                actions.remove(action)

        model._meta.verbose_name_plural = 'Gestion des impacts'

        context = {
            'model': model,
            'table': table,
            'actions': actions,
            'filter_form': self.filterset_form(request.GET, label_suffix='') if self.filterset_form else None,
            'prerequisite_model': get_prerequisite_model(self.queryset),
            **self.get_extra_context(request),
        }

        return render(request, self.template_name, context)


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
