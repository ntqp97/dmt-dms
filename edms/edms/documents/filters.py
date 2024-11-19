import django_filters
from .models import Document, DocumentReceiver, DocumentSignature
from ..search.filters import UnaccentFilter

DOCUMENT_CLASSIFICATION_CHOICES = (
    ('created', 'Created by me'),
    ('received', 'Received by me'),
    ('forwarded', 'Forwarded by me'),
    ('unread', 'Received but unread by me'),
    ('pending_signing', 'Pending my signature'),
    ('pending_initial_signing', 'Pending my initial signature'),
)


class DocumentFilter(django_filters.FilterSet):
    document_code = django_filters.CharFilter(lookup_expr='icontains')
    document_title = UnaccentFilter(field_name='document_title')
    document_summary = UnaccentFilter(field_name='document_summary')
    document_type = django_filters.CharFilter(lookup_expr='exact')
    urgency_status = django_filters.CharFilter(lookup_expr='exact')
    security_type = django_filters.CharFilter(lookup_expr='exact')
    publish_type = django_filters.CharFilter(lookup_expr='exact')
    sector = django_filters.CharFilter(lookup_expr='exact')
    document_form = django_filters.CharFilter(lookup_expr='exact')
    processing_status = django_filters.CharFilter(lookup_expr='exact')
    document_number_reference_code = UnaccentFilter(field_name='document_number_reference_code')
    document_category = django_filters.CharFilter(lookup_expr='exact')
    documents_statistics = django_filters.ChoiceFilter(
        choices=DOCUMENT_CLASSIFICATION_CHOICES, method='filter_by_classification'
    )
    created_at = django_filters.DateFromToRangeFilter()

    class Meta:
        model = Document
        fields = [
            'document_code',
            'document_title',
            'document_summary',
            'document_type',
            'urgency_status',
            'security_type',
            'publish_type',
            'sector',
            'document_form',
            'processing_status',
            'document_number_reference_code',
            'created_at',
            'documents_statistics',
            # 'document_processing_deadline_at',
            # 'receivers',
        ]

    def filter_by_classification(self, queryset, name, value):
        user = self.request.user
        if value == 'created':
            return queryset.filter(
                created_by=user,
                # document_category__in=[
                #     Document.NORMAL_DOCUMENT,
                #     Document.COMPLETED_SIGNING_DOCUMENT,
                # ]
            )
        elif value == 'received':
            return queryset.filter(document_receivers__receiver=user).distinct()
        elif value == 'forwarded':
            return queryset.filter(
                document_receivers__created_by=user,
            ).exclude(
                document_receivers__receiver=user,
            ).distinct()
        elif value == 'unread':
            return queryset.filter(
                document_receivers__receiver=user,
                document_receivers__is_read=False
            ).distinct()
        elif value == 'pending_signing':
            return queryset.filter(
                document_category=Document.IN_PROGRESS_SIGNING_DOCUMENT,
                signatures__signer=user,
                signatures__signature_status__in=[
                    DocumentSignature.UNSIGNED,
                    DocumentSignature.FAILED,
                    DocumentSignature.TIMEOUT,
                ],
                signatures__is_signature_visible=True
            ).distinct()
        elif value == 'pending_initial_signing':
            return queryset.filter(
                document_category=Document.IN_PROGRESS_SIGNING_DOCUMENT,
                signatures__signer=user,
                signatures__signature_status__in=[
                    DocumentSignature.UNSIGNED,
                    DocumentSignature.FAILED,
                    DocumentSignature.TIMEOUT,
                ],
                signatures__is_signature_visible=False
            ).distinct()
        return queryset
