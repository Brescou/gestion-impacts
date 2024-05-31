# Generated by Django 5.0.6 on 2024-05-23 19:43

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gestion_impacts', '0002_alter_impact_options_impact_vm'),
        ('ipam', '0069_gfk_indexes'),
    ]

    operations = [
        migrations.RenameField(
            model_name='impact',
            old_name='name',
            new_name='impact',
        ),
        migrations.AddField(
            model_name='impact',
            name='description',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='impact',
            name='vrf',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='ipam.vrf'),
        ),
        migrations.AlterUniqueTogether(
            name='impact',
            unique_together={('ip_address', 'vrf')},
        ),
    ]
