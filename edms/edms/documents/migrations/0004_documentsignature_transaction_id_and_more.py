# Generated by Django 5.0.8 on 2024-10-21 13:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('documents', '0003_document_attachment_documents'),
    ]

    operations = [
        migrations.AddField(
            model_name='documentsignature',
            name='transaction_id',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='document',
            name='document_category',
            field=models.CharField(blank=True, choices=[('signing_document', 'signing_document'), ('normal_document', 'normal_document'), ('in_progress_signing_document', 'in_progress_signing_document'), ('completed_signing_document', 'completed_signing_document')], default='normal_document', max_length=255, null=True),
        ),
    ]
