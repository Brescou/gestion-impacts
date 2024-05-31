from dcim.models import Interface
from django.contrib.contenttypes.models import ContentType
from django.db.models import Case, When, Value, CharField, Subquery, OuterRef, Func, F, JSONField, ExpressionWrapper
from ipam.models import IPAddress
from netbox.views import generic
from virtualization.models import VMInterface

from .filtersets import ImpactFilterSet
from .forms import ImpactForm, ImpactBulkImportForm, ImpactBulkEditForm
from .models import Impact
from .tables import ImpactTable


class ImpactView(generic.ObjectView):
    queryset = Impact.objects.all()


class ImpactListView(generic.ObjectListView):
    queryset = IPAddress.objects.annotate(
        cf_nom_long=ExpressionWrapper(
            Func(F('custom_field_data'), Value('nom_long'), function='jsonb_extract_path_text'),
            output_field=CharField()
        )
    ).annotate(
        assigned_to=Case(
            When(
                assigned_object_type=ContentType.objects.get_for_model(Interface),
                then=Subquery(
                    Interface.objects.filter(pk=OuterRef('assigned_object_id')).values('device__name')[:1]
                )
            ),
            When(
                assigned_object_type=ContentType.objects.get_for_model(VMInterface),
                then=Subquery(
                    VMInterface.objects.filter(pk=OuterRef('assigned_object_id')).values('virtual_machine__name')[:1]
                )
            ),
            default=F('cf_nom_long'),
            output_field=CharField(),
        )
    )
    table = ImpactTable


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
