from django import forms
from ipam.models import IPAddress, VRF
from netbox.forms import NetBoxModelForm, NetBoxModelImportForm, NetBoxModelBulkEditForm, NetBoxModelFilterSetForm

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
        fields = ('impact', 'redundancy')

    impact = forms.CharField(help_text='LL', required=True)
    redundancy = forms.BooleanField(required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields.pop('tags', None)

    def save(self, ip_address=None, commit=True):
        if self.errors:
            raise ValueError(
                "The %s could not be %s because the data didn't validate."
                % (
                    self.instance._meta.object_name,
                    "created" if self.instance._state.adding else "changed",
                )
            )
        if commit:
            address = IPAddress.objects.filter(pk=ip_address).first()
            if not address:
                raise ValueError("IP address not found")
            self.instance.ip_address = address
            if not address.vrf:
                raise ValueError("IP address has no VRF")
            self.instance.vrf = address.vrf
            self.instance.save()
            self._save_m2m()
        else:
            self.save_m2m = self._save_m2m
        return self.instance


class ImpactBulkImportForm(NetBoxModelImportForm):
    class Meta:
        model = Impact
        fields = ('impact', 'redundancy', 'ip_address')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields.pop('tags', None)


class ImpactBulkEditForm(NetBoxModelBulkEditForm):
    model = Impact
    impact = forms.CharField(required=False)
    redundancy = forms.BooleanField(required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields.pop('add_tags', None)
        self.fields.pop('remove_tags', None)
