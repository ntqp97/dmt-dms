# Generated by Django 5.0.8 on 2024-11-19 16:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('documents', '0005_alter_documentsignature_signature_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='document',
            name='deleted',
            field=models.BooleanField(default=False),
        ),
    ]
