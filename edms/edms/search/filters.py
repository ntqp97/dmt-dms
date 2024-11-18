from rest_framework.filters import SearchFilter
from django.db.models import Func, Q
from text_unidecode import unidecode
import django_filters


class Unaccent(Func):
    function = 'unaccent'


class UnaccentSearchFilter(SearchFilter):
    """
    Custom SearchFilter to support both accented and unaccented searches.
    """
    def construct_search(self, field_name):
        return f"{field_name}__icontains"

    def filter_queryset(self, request, queryset, view):
        search_terms = self.get_search_terms(request)
        if not search_terms:
            return queryset

        search_fields = getattr(view, 'search_fields', None)
        if not search_fields:
            return queryset

        conditions = Q()
        for term in search_terms:
            normalized_term = unidecode(term)
            term_conditions = Q()
            for field in search_fields:
                # Annotate field with unaccent
                annotated_field = f"normalized_{field.replace('.', '_')}"
                queryset = queryset.annotate(**{annotated_field: Unaccent(field)})
                # Add conditions for both accented and unaccented searches
                term_conditions |= Q(**{self.construct_search(field): term})
                term_conditions |= Q(**{self.construct_search(annotated_field): normalized_term})
            conditions &= term_conditions

        return queryset.filter(conditions)


class UnaccentFilter(django_filters.CharFilter):
    """
    Custom filter that supports searching both with and without accents.
    """
    def filter(self, queryset, value):
        if not value:
            return queryset

        # Normalize the search value (remove accents)
        normalized_value = unidecode(value)

        # Annotate field with unaccent
        annotated_field = f"normalized_{self.field_name}"
        queryset = queryset.annotate(**{annotated_field: Unaccent(self.field_name)})

        # Perform the search
        return queryset.filter(
            Q(**{f"{self.field_name}__icontains": value}) |  # Match with accents
            Q(**{f"{annotated_field}__icontains": normalized_value})  # Match without accents
        )


class NumberInFilter(django_filters.BaseInFilter, django_filters.NumberFilter):
    pass
