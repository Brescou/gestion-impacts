import logging

from core.models import ObjectType
from dcim.models import Device
from django.contrib import messages
from django.contrib.contenttypes.fields import GenericRel
from django.core.exceptions import FieldDoesNotExist
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import F, Value, CharField, Q, OuterRef, Subquery
from django.db.models import ManyToManyField
from django.db.models.fields.json import KeyTextTransform
from django.db.models.fields.reverse_related import ManyToManyRel
from django.db.models.functions import Coalesce
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.utils.html import escape
from django.utils.safestring import mark_safe
from extras.models import ExportTemplate
from extras.signals import clear_events
from ipam.models import IPAddress
from netbox.views import generic
from netbox.views.generic.utils import get_prerequisite_model
from utilities.exceptions import AbortRequest, PermissionsViolation
from utilities.forms import restrict_form_fields
from utilities.htmx import htmx_partial
from utilities.querydict import prepare_cloned_fields, normalize_querydict
from virtualization.models import VirtualMachine

from .filtersets import ImpactFilterSet
from .forms import ImpactForm, ImpactBulkEditForm, ImpactIpAddressFilterSetForm
from .models import Impact
from .tables import ImpactTable


class ImpactView(generic.ObjectView):
    queryset = Impact.objects.all()


def get_ip_address_queryset():
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
        impact_id=Subquery(
            Impact.objects.filter(ip_address=OuterRef('pk')).values('id')[:1]
        ),
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
    return queryset


class ImpactListView(generic.ObjectListView):
    queryset = get_ip_address_queryset()

    table = ImpactTable
    template_name = 'gestion_impacts/impact_list.html'
    filterset = ImpactFilterSet
    filterset_form = ImpactIpAddressFilterSetForm

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return self.filterset(self.request.GET, queryset=queryset).qs

    def get(self, request):
        model = self.queryset.model
        object_type = ObjectType.objects.get_for_model(model)

        if self.filterset:
            self.queryset = self.filterset(request.GET, self.queryset, request=request).qs

        actions = self.get_permitted_actions(request.user)
        has_bulk_actions = any([a.startswith('bulk_') for a in actions])

        if 'export' in request.GET:

            if request.GET['export'] == 'table':
                table = self.get_table(self.queryset, request, has_bulk_actions)
                columns = [name for name, _ in table.selected_columns]
                return self.export_table(table, columns)

            elif request.GET['export']:
                template = get_object_or_404(ExportTemplate, object_types=object_type, name=request.GET['export'])
                return self.export_template(template, request)

            elif hasattr(model, 'to_yaml'):
                response = HttpResponse(self.export_yaml(), content_type='text/yaml')
                filename = 'netbox_{}.yaml'.format(self.queryset.model._meta.verbose_name_plural)
                response['Content-Disposition'] = 'attachment; filename="{}"'.format(filename)
                return response

            else:
                table = self.get_table(self.queryset, request, has_bulk_actions)
                return self.export_table(table)

        table = self.get_table(self.queryset, request, has_bulk_actions)

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
            'extra_model': Impact(),
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
    template_name = 'gestion_impacts/impact_edit.html'

    def get(self, request, *args, **kwargs):

        obj = self.get_object(**kwargs)
        obj = self.alter_object(obj, request, args, kwargs)
        model = self.queryset.model

        initial_data = normalize_querydict(request.GET)
        form = self.form(instance=obj, initial=initial_data)
        restrict_form_fields(form, request.user)

        return render(request, self.template_name, {
            'model': model,
            'object': obj,
            'form': form,
            'return_url': self.get_return_url(request, obj),
            'prerequisite_model': get_prerequisite_model(self.queryset),
            "assigned_to": request.GET.get('assigned_to'),
            **self.get_extra_context(request, obj),
        })

    def post(self, request, *args, **kwargs):

        logger = logging.getLogger('netbox.views.ObjectEditView')
        obj = self.get_object(**kwargs)

        # Take a snapshot for change logging (if editing an existing object)
        if obj.pk and hasattr(obj, 'snapshot'):
            obj.snapshot()

        obj = self.alter_object(obj, request, args, kwargs)

        form = self.form(data=request.POST, files=request.FILES, instance=obj)
        restrict_form_fields(form, request.user)

        if form.is_valid():
            logger.debug("Form validation was successful")

            try:
                with transaction.atomic():
                    object_created = form.instance.pk is None
                    obj = form.save(ip_address=request.GET.get('ip_address'))

                    # Check that the new object conforms with any assigned object-level permissions
                    if not self.queryset.filter(pk=obj.pk).exists():
                        raise PermissionsViolation()

                msg = '{} {}'.format(
                    'Created' if object_created else 'Modified',
                    self.queryset.model._meta.verbose_name
                )
                logger.info(f"{msg} {obj} (PK: {obj.pk})")
                if hasattr(obj, 'get_absolute_url'):
                    msg = mark_safe(f'{msg} <a href="{obj.get_absolute_url()}">{escape(obj)}</a>')
                else:
                    msg = f'{msg} {obj}'
                messages.success(request, msg)

                if '_addanother' in request.POST:
                    redirect_url = request.path

                    # If cloning is supported, pre-populate a new instance of the form
                    params = prepare_cloned_fields(obj)
                    params.update(self.get_extra_addanother_params(request))
                    if params:
                        if 'return_url' in request.GET:
                            params['return_url'] = request.GET.get('return_url')
                        redirect_url += f"?{params.urlencode()}"

                    return redirect(redirect_url)

                return_url = self.get_return_url(request, obj)

                return redirect(return_url)

            except (AbortRequest, PermissionsViolation) as e:
                logger.debug(e.message)
                form.add_error(None, e.message)
                clear_events.send(sender=self)

        else:
            logger.debug("Form validation failed")

        return render(request, self.template_name, {
            'object': obj,
            'form': form,
            'return_url': self.get_return_url(request, obj),
            **self.get_extra_context(request, obj),
        })


class ImpactDeleteView(generic.ObjectDeleteView):
    queryset = Impact.objects.all()


class ImpactBulkEditView(generic.BulkEditView):
    queryset = get_ip_address_queryset()

    form = ImpactBulkEditForm
    table = ImpactTable
    filterset = ImpactFilterSet

    def _update_objects(self, form, request):
        custom_fields = getattr(form, 'custom_fields', {})
        standard_fields = [
            field for field in form.fields if field not in list(custom_fields) + ['pk']
        ]
        nullified_fields = request.POST.getlist('_nullify')
        updated_objects = []
        model_fields = {}
        m2m_fields = {}

        # Build list of model fields and m2m fields for later iteration
        for name in standard_fields:
            try:
                model_field = Impact._meta.get_field(name)
                if isinstance(model_field, (ManyToManyField, ManyToManyRel)):
                    m2m_fields[name] = model_field
                elif isinstance(model_field, GenericRel):
                    continue
                else:
                    model_fields[name] = model_field
            except FieldDoesNotExist:
                model_fields[name] = None

        for obj in self.queryset.filter(pk__in=form.cleaned_data['pk']):
            # Get or create the Impact object for each IP address
            impact, created = Impact.objects.get_or_create(ip_address=obj)

            # Take a snapshot of change-logged models
            if hasattr(impact, 'snapshot'):
                impact.snapshot()

            # Update standard fields
            for name, model_field in model_fields.items():
                if name in form.nullable_fields and name in nullified_fields:
                    setattr(impact, name, None if model_field.null else '')
                elif name in form.changed_data:
                    setattr(impact, name, form.cleaned_data[name])

            # Update custom fields
            for name, customfield in custom_fields.items():
                assert name.startswith('cf_')
                cf_name = name[3:]
                if name in form.nullable_fields and name in nullified_fields:
                    impact.custom_field_data[cf_name] = None
                elif name in form.changed_data:
                    impact.custom_field_data[cf_name] = customfield.serialize(form.cleaned_data[name])

            impact.full_clean()
            impact.save()
            updated_objects.append(impact)

            # Handle M2M fields after save
            for name, m2m_field in m2m_fields.items():
                if name in form.nullable_fields and name in nullified_fields:
                    getattr(impact, name).clear()
                elif form.cleaned_data[name]:
                    getattr(impact, name).set(form.cleaned_data[name])

            # Add/remove tags
            if form.cleaned_data.get('add_tags', None):
                impact.tags.add(*form.cleaned_data['add_tags'])
            if form.cleaned_data.get('remove_tags', None):
                impact.tags.remove(*form.cleaned_data['remove_tags'])

        return updated_objects

    def post(self, request, **kwargs):
        logger = logging.getLogger('netbox.views.BulkEditView')
        model = IPAddress

        if request.POST.get('_all') and self.filterset is not None:
            pk_list = self.filterset(request.GET, self.queryset.values_list('pk', flat=True), request=request).qs
        else:
            pk_list = request.POST.getlist('pk')

        initial_data = {'pk': pk_list}

        if '_apply' in request.POST:
            form = self.form(request.POST, initial=initial_data)
            restrict_form_fields(form, request.user)

            if form.is_valid():
                logger.debug("Form validation was successful")

                try:
                    with transaction.atomic():
                        updated_objects = self._update_objects(form, request)

                        object_count = Impact.objects.filter(pk__in=[obj.pk for obj in updated_objects]).count()
                        if object_count != len(updated_objects):
                            raise PermissionsViolation

                    if updated_objects:
                        msg = f'Updated {len(updated_objects)} {model._meta.verbose_name_plural}'
                        logger.info(msg)
                        messages.success(self.request, msg)

                    return redirect(self.get_return_url(request))

                except ValidationError as e:
                    messages.error(self.request, ", ".join(e.messages))
                    clear_events.send(sender=self)

                except (AbortRequest, PermissionsViolation) as e:
                    logger.debug(e.message)
                    form.add_error(None, e.message)
                    clear_events.send(sender=self)

            else:
                logger.debug("Form validation failed")

        else:
            form = self.form(initial=initial_data)
            restrict_form_fields(form, request.user)

        table = self.table(self.queryset.filter(pk__in=pk_list), orderable=False)
        if not table.rows:
            messages.warning(request, f"No {model._meta.verbose_name_plural} were selected.")
            return redirect(self.get_return_url(request))
        columns_to_remove = ['device_name', 'vm_name', 'actions']
        for column in columns_to_remove:
            if column in table.base_columns:
                table.columns.hide(column)

        return render(request, self.template_name, {
            'model': model,
            'form': form,
            'table': table,
            'return_url': self.get_return_url(request),
            **self.get_extra_context(request),
        })


class ImpactBulkDeleteView(generic.BulkDeleteView):
    queryset = Impact.objects.all()
    table = ImpactTable
