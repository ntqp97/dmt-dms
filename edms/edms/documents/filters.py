import django_filters
from .models import Document, DocumentReceiver
from ..search.filters import UnaccentFilter


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
            # 'document_processing_deadline_at',
            # 'receivers',
        ]

