from dcim.models import Device
from django import forms
from ipam.models import IPAddress, VRF
from netbox.forms import NetBoxModelForm, NetBoxModelImportForm, NetBoxModelBulkEditForm, NetBoxModelFilterSetForm
from utilities.forms.fields import DynamicModelChoiceField
from virtualization.models import VirtualMachine

from .models import Impact


class ImpactIpAddressFilterSetForm(NetBoxModelFilterSetForm):
    vrf = forms.ModelChoiceField(queryset=VRF.objects.all(), required=False)
    model = IPAddress

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields.pop('cf_interface', None)
        self.fields.pop('cf_source', None)
        self.fields.pop('cf_redondance', None)
        self.fields.pop('cf_impact_exploitation', None)
        self.fields.pop('cf_nom_long', None)
        self.custom_fields = None
        self.custom_field_groups = None


class ImpactForm(NetBoxModelForm):
    class Meta:
        model = Impact
        fields = ('impact', 'redundancy', 'ip_address', 'vrf')

    impact = forms.CharField(help_text='Ceci est l\'endroit pour decrire comment rediger un impact')
    redundancy = forms.BooleanField(required=False)
    ip_address = DynamicModelChoiceField(queryset=IPAddress.objects.all(), required=False)
    vrf = DynamicModelChoiceField(queryset=VRF.objects.all(), required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields.pop('tags', None)

    # def clean(self):
    #     device = self.cleaned_data.get('device')
    #     ip_address = self.cleaned_data.get('ip_address')
    #     vm = self.cleaned_data.get('vm')
    #     if not device and not ip_address and not vm:
    #         raise forms.ValidationError('You must select a device, an IP address or a VM')
    #     if (device and ip_address) or (device and vm) or (ip_address and vm):
    #         raise forms.ValidationError('You cannot select more than one of device, IP address, or VM.')
    #     return self.cleaned_data


class ImpactBulkImportForm(NetBoxModelImportForm):
    class Meta:
        model = Impact
        fields = ('impact', 'redundancy', 'ip_address')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields.pop('tags', None)

    # def clean(self):
    #     cleaned_data = super().clean()
    #     device = cleaned_data.get('device')
    #     ip_address = cleaned_data.get('ip_address')
    #     vm = cleaned_data.get('vm')
    #
    #     if not device and not ip_address and not vm:
    #         raise forms.ValidationError('You must select a device, an IP address, or a VM.')
    #     if (device and ip_address) or (device and vm) or (ip_address and vm):
    #         raise forms.ValidationError('You cannot select more than one of device, IP address, or VM.')
    #
    #     return cleaned_data


class ImpactBulkEditForm(NetBoxModelBulkEditForm):
    model = Impact
    impact = forms.CharField(required=False)
    redundancy = forms.BooleanField(required=False)
    # device = DynamicModelChoiceField(queryset=Device.objects.all(), required=False)
    ip_address = DynamicModelChoiceField(queryset=IPAddress.objects.all(), required=False)

    # vm = DynamicModelChoiceField(queryset=VirtualMachine.objects.all(), required=False)

    # nullable_fields = ('device', 'ip_address', 'vm')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields.pop('add_tags', None)
        self.fields.pop('remove_tags', None)

    # def clean(self):
    #     cleaned_data = super().clean()
    #     device = cleaned_data.get('device')
    #     ip_address = cleaned_data.get('ip_address')
    #     vm = cleaned_data.get('vm')
    #
    #     if not device and not ip_address and not vm:
    #         raise forms.ValidationError('You must select a device, an IP address, or a VM.')
    #     if (device and ip_address) or (device and vm) or (ip_address and vm):
    #         raise forms.ValidationError('You cannot select more than one of device, IP address, or VM.')
    #
    #     return cleaned_data

    # def save(self, commit=True):
    #     instances = super().save(commit=False)
    #     for instance in instances:
    #         if self.cleaned_data.get('device'):
    #             instance.ip_address = None
    #             instance.vm = None
    #         elif self.cleaned_data.get('ip_address'):
    #             instance.device = None
    #             instance.vm = None
    #         elif self.cleaned_data.get('vm'):
    #             instance.device = None
    #             instance.ip_address = None
    #         if commit:
    #             instance.save()
    #     return instances
