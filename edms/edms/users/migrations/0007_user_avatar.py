# Generated by Django 5.0.8 on 2024-12-30 15:34

import edms.common.storage_backends
import edms.users.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0006_user_birthdate'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='avatar',
            field=models.FileField(blank=True, default=None, null=True, storage=edms.common.storage_backends.PublicMediaStorage(), upload_to=edms.users.models.get_path_user_avatar),
        ),
    ]
