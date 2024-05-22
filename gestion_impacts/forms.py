from dcim.models import Device
from django import forms
from ipam.models import IPAddress
from netbox.forms import NetBoxModelForm, NetBoxModelImportForm, NetBoxModelBulkEditForm
from utilities.forms.fields import DynamicModelChoiceField
from virtualization.models import VirtualMachine

from .models import Impact


# TODO BULK IMPORT CSV / Direct Import , ; or \t

class ImpactForm(NetBoxModelForm):
    class Meta:
        model = Impact
        fields = ('name', 'redundancy', 'device', 'ip_address', 'vm')

    device = DynamicModelChoiceField(queryset=Device.objects.all(), required=False)
    ip_address = DynamicModelChoiceField(queryset=IPAddress.objects.all(), required=False)
    vm = DynamicModelChoiceField(queryset=VirtualMachine.objects.all(), required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields.pop('tags', None)

    def clean(self):
        device = self.cleaned_data.get('device')
        ip_address = self.cleaned_data.get('ip_address')
        vm = self.cleaned_data.get('vm')
        if not device and not ip_address and not vm:
            raise forms.ValidationError('You must select a device, an IP address or a VM')
        if (device and ip_address) or (device and vm) or (ip_address and vm):
            raise forms.ValidationError('You cannot select more than one of device, IP address, or VM.')
        return self.cleaned_data


class ImpactBulkImportForm(NetBoxModelImportForm):
    class Meta:
        model = Impact
        fields = ('name', 'redundancy', 'device', 'ip_address', 'vm')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields.pop('tags', None)

    def clean(self):
        cleaned_data = super().clean()
        device = cleaned_data.get('device')
        ip_address = cleaned_data.get('ip_address')
        vm = cleaned_data.get('vm')

        if not device and not ip_address and not vm:
            raise forms.ValidationError('You must select a device, an IP address, or a VM.')
        if (device and ip_address) or (device and vm) or (ip_address and vm):
            raise forms.ValidationError('You cannot select more than one of device, IP address, or VM.')

        return cleaned_data


class ImpactBulkEditForm(NetBoxModelBulkEditForm):
    model = Impact
    name = forms.CharField(required=False)
    redundancy = forms.NullBooleanField(required=False)
    device = DynamicModelChoiceField(queryset=Device.objects.all(), required=False)
    ip_address = DynamicModelChoiceField(queryset=IPAddress.objects.all(), required=False)
    vm = DynamicModelChoiceField(queryset=VirtualMachine.objects.all(), required=False)

    nullable_fields = ('device', 'ip_address', 'vm')
