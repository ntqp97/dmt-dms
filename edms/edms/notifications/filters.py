import django_filters
from .models import Notification, NotificationReceiver


class NotificationFilter(django_filters.FilterSet):
    is_read = django_filters.BooleanFilter(method='filter_is_read')

    class Meta:
        model = Notification
        fields = [
            'is_read',
        ]

    def filter_is_read(self, queryset, name, value):
        user = self.request.user
        return queryset.filter(
            notification_receivers__receiver=user,
            notification_receivers__is_read=value
        ).distinct()
