import django_filters
from edms.users.models import User
from edms.search.filters import UnaccentFilter, NumberInFilter


class UserFilter(django_filters.FilterSet):
    name = UnaccentFilter(field_name='name')
    email = UnaccentFilter(field_name='email')
    phone_number = django_filters.CharFilter(lookup_expr='exact')
    position = UnaccentFilter(field_name='position')
    gender = django_filters.BooleanFilter()
    organization_unit = NumberInFilter(
        field_name='organization_unit__id',
        lookup_expr='in',
        distinct=True,
    )

    class Meta:
        model = User
        fields = [
            "name",
            "email",
            "phone_number",
            "position",
            "gender",
            "organization_unit"
        ]
