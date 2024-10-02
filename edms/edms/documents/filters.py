import django_filters
from .models import Document, DocumentReceiver


class DocumentFilter(django_filters.FilterSet):
    document_code = django_filters.CharFilter(lookup_expr='icontains')
    document_title = django_filters.CharFilter(lookup_expr='icontains')
    document_type = django_filters.CharFilter(lookup_expr='exact')
    urgency_status = django_filters.CharFilter(lookup_expr='exact')
    security_type = django_filters.CharFilter(lookup_expr='exact')
    publish_type = django_filters.CharFilter(lookup_expr='exact')
    sector = django_filters.CharFilter(lookup_expr='exact')
    processing_status = django_filters.CharFilter(lookup_expr='exact')
    document_number_reference_code = django_filters.CharFilter(lookup_expr='icontains')
    document_category = django_filters.CharFilter(lookup_expr='exact')

    # document_processing_deadline_at = django_filters.NumberFilter(field_name='document_processing_deadline_at')  # Lọc theo deadline
    # receivers = django_filters.ModelMultipleChoiceFilter(
    #     field_name='receivers',
    #     queryset=User.objects.all(),
    #     to_field_name='id',  # Lọc theo người nhận bằng ID
    # )

    class Meta:
        model = Document
        fields = [
            'document_code',
            'document_title',
            'document_type',
            'urgency_status',
            'security_type',
            'publish_type',
            'sector',
            'processing_status',
            # 'document_processing_deadline_at',
            # 'receivers',
        ]

