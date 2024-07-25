from django import forms
from django.forms import ModelMultipleChoiceField
from ipam.models import IPAddress, VRF
from jsonschema.exceptions import ValidationError
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

    impact = forms.CharField(help_text='A remplir *', required=True)
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
            if ip_address:
                self.instance.ip_address = ip_address
                self.instance.vrf = ip_address.vrf
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


class IPAddressMultipleChoiceField(ModelMultipleChoiceField):
    def _check_values(self, value):
        key = self.to_field_name or "pk"
        try:
            value = frozenset(value)
        except TypeError:
            raise ValidationError(
                self.error_messages["invalid_list"],
                code="invalid_list",
            )
        valid_pks = set(IPAddress.objects.filter(pk__in=value).values_list('pk', flat=True))
        invalid_pks = value - {str(pk) for pk in valid_pks}
        if invalid_pks:
            raise ValidationError(
                self.error_messages["invalid_pk_value"],
                code="invalid_pk_value",
                params={"pk": ", ".join(map(str, invalid_pks))}
            )
        qs = IPAddress.objects.filter(pk__in=value)
        return qs


class ImpactBulkEditForm(NetBoxModelBulkEditForm):
    model = Impact
    impact = forms.CharField(required=False)
    redundancy = forms.BooleanField(required=False)
    pk = IPAddressMultipleChoiceField(
        queryset=IPAddress.objects.all(),
        widget=forms.MultipleHiddenInput()
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields.pop('add_tags', None)
        self.fields.pop('remove_tags', None)

    # vrf
