# Generated by Django 5.0.6 on 2024-05-21 18:20

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gestion_impacts', '0001_initial'),
        ('virtualization', '0038_virtualdisk'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='impact',
            options={},
        ),
        migrations.AddField(
            model_name='impact',
            name='vm',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='virtualization.virtualmachine'),
        ),
    ]
