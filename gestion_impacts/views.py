from netbox.views import generic

from .filtersets import ImpactFilterSet
from .forms import ImpactForm, ImpactBulkImportForm
from .models import Impact
from .tables import ImpactTable


class ImpactView(generic.ObjectView):
    queryset = Impact.objects.all()


class ImpactListView(generic.ObjectListView):
    queryset = Impact.objects.all()
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
    model_form = ImpactForm
    table = ImpactTable
    filterset = ImpactFilterSet
