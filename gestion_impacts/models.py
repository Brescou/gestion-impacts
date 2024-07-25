from django.db import models
from django.urls import reverse
from django.conf import settings

from netbox.models import NetBoxModel


class Impact(NetBoxModel):
    impact = models.TextField(help_text='Impact')
    redundancy = models.BooleanField(default=False)
    ip_address = models.ForeignKey('ipam.IPAddress', on_delete=models.CASCADE, null=True, blank=True,
                                   related_name='ipaddress')
    vrf = models.ForeignKey('ipam.VRF', on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return f""

    def get_absolute_url(self):
        return reverse('plugins:gestion_impacts:impact', args=[self.pk])


