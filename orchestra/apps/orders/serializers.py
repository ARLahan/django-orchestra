from rest_framework import serializers

from orchestra.apps.accounts.serializers import AccountSerializerMixin

from .models import Order


class OrderSerializer(AccountSerializerMixin, serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Order
        fields = (
            'url', 'registered_on', 'cancelled_on', 'billed_on', 'billed_until',
            'description'
        )
