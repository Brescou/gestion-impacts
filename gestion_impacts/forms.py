from django import forms
from django.forms import ModelMultipleChoiceField
from django.forms.utils import ErrorDict
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


class IPAddressMultipleChoiceField(ModelMultipleChoiceField):
    def _check_values(self, value):
        """
        Given a list of possible PK values, return a QuerySet of the
        corresponding objects. Raise a ValidationError if a given value is
        invalid (not a valid PK, not in the queryset, etc.)
        """
        key = self.to_field_name or "pk"
        # Deduplicate given values to avoid creating many querysets or
        # requiring the database backend to deduplicate efficiently.
        try:
            value = frozenset(value)
        except TypeError:
            # list of lists isn't hashable, for example
            raise ValidationError(
                self.error_messages["invalid_list"],
                code="invalid_list",
            )

        # Validate that each pk in value corresponds to an existing IPAddress
        valid_pks = set(IPAddress.objects.filter(pk__in=value).values_list('pk', flat=True))
        invalid_pks = value - {str(pk) for pk in valid_pks}
        if invalid_pks:
            raise ValidationError(
                self.error_messages["invalid_pk_value"],
                code="invalid_pk_value",
                params={"pk": ", ".join(map(str, invalid_pks))}
            )

        # Now return the IPAddress queryset filtering by IP addresses
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

    @property
    def errors(self):
        """Return an ErrorDict for the data provided for the form."""
        if self._errors is None:
            self.full_clean()
        return self._errors

    def is_valid(self):
        """Return True if the form has no errors, or False otherwise."""
        return self.is_bound and not self.errors

    def full_clean(self):
        """
        Clean all of self.data and populate self._errors and self.cleaned_data.
        """
        self._errors = ErrorDict()
        if not self.is_bound:  # Stop further processing.
            return
        self.cleaned_data = {}
        # If the form is permitted to be empty, and none of the form data has
        # changed from the initial data, short circuit any validation.
        if self.empty_permitted and not self.has_changed():
            return

        self._clean_fields()
        self._clean_form()
        self._post_clean()
