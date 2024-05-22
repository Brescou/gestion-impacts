from django.db import models
from django.urls import reverse

from netbox.models import NetBoxModel


class Impact(NetBoxModel):
    name = models.CharField(max_length=200)
    redundancy = models.BooleanField(default=False)
    ip_address = models.ForeignKey('ipam.IPAddress', on_delete=models.CASCADE, null=True, blank=True)
    device = models.ForeignKey('dcim.Device', on_delete=models.CASCADE, null=True, blank=True)
    vm = models.ForeignKey('virtualization.VirtualMachine', on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('plugins:gestion_impacts:impact', args=[self.pk])
