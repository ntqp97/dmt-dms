# Register your models here.
from django.contrib import admin
from .models import Document, DocumentReceiver, DocumentSignature


@admin.register(DocumentReceiver)
class DocumentReceiverAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "document",
        "receiver",
        "is_read",
        "read_at",
    )
    ordering = ("-id",)
    list_filter = ("is_read",)


@admin.register(DocumentSignature)
class DocumentSignatureAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "document",
        "signer",
        "order",
        "signature_status",
        "is_signature_visible",
        "transaction_id",
    )
    ordering = ("document", "id")
    fieldsets = (
        (None, {
            "fields": (
                "document",
                "signer",
                "order",
                "signature_status",
                "is_signature_visible",
                "transaction_id",
            )
        }),
    )


class DocumentReceiverInline(admin.TabularInline):
    model = DocumentReceiver
    extra = 1


class DocumentSignatureInline(admin.TabularInline):
    model = DocumentSignature
    extra = 1


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "document_code",
        "document_title",
        "document_type",
        "urgency_status",
        "document_category",
        "processing_status",
        "document_processing_deadline_at",
    )
    list_filter = (
        "document_type",
        "urgency_status",
        "document_category",
        "processing_status",
    )
    search_fields = ("document_code", "document_title")
    ordering = ("-id",)
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        (None, {
            "fields": (
                "document_code",
                "document_title",
                "document_summary",
                "document_type",
                "urgency_status",
                "document_form",
                "security_type",
                "document_processing_deadline_at",
                "publish_type",
                "document_number_reference_code",
                "sector",
                "processing_status",
                "document_category",
            )
        }),
        ("Attachments", {
            "fields": ("files", "attachment_documents"),
        }),
    )
    inlines = [DocumentReceiverInline, DocumentSignatureInline]
