# Generated by Django 5.0.8 on 2024-09-04 08:52

import django.db.models.deletion
import edms.assets.models
import edms.common.storage_backends
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Asset',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, null=True)),
                ('updated_at', models.DateTimeField(auto_now=True, null=True)),
                ('file', models.FileField(blank=True, default=None, null=True, storage=edms.common.storage_backends.PrivateMediaStorage, upload_to=edms.assets.models.get_path_files)),
                ('size', models.BigIntegerField()),
                ('mime_type', models.CharField(max_length=255)),
                ('asset_name', models.CharField(max_length=255)),
                ('file_type', models.CharField(blank=True, choices=[('attachment', 'attachment'), ('appendix', 'appendix')], default='attachment', max_length=255, null=True)),
                ('created_by', models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='created_%(class)ss', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
    ]