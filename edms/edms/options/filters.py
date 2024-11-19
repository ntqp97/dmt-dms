import django_filters

from edms.options.models import Option


class OptionFilter(django_filters.FilterSet):
    type = django_filters.CharFilter(lookup_expr='exact')

    class Meta:
        model = Option
        fields = [
            "type",
        ]
