from django.db import models
from django.urls import reverse

from netbox.models import NetBoxModel


class Impact(NetBoxModel):
    impact = models.TextField(help_text='Impact')
    redundancy = models.BooleanField(default=False)
    ip_address = models.ForeignKey('ipam.IPAddress', on_delete=models.CASCADE, null=True, blank=True,
                                   related_name='ipaddress')
    vrf = models.ForeignKey('ipam.VRF', on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return self.impact

    def get_absolute_url(self):
        return reverse('plugins:gestion_impacts:impact', args=[self.pk])


# class ViewImpactIPAddress(models.Model):
#     impact_id = models.IntegerField(primary_key=True)
#     impact = models.TextField()
#     redundancy = models.BooleanField()
#     ip_address = models.CharField(max_length=15)
#     vrf = models.CharField(max_length=100)
#
#     class Meta:
#         managed = False
#         db_table = 'view_impact_ipaddress'
