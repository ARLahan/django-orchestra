from rest_framework import serializers

from orchestra.apps.accounts.serializers import AccountSerializerMixin

from .methods import PaymentMethod
from .models import PaymentSource, Transaction


class PaymentSourceSerializer(AccountSerializerMixin, serializers.HyperlinkedModelSerializer):
    class Meta:
        model = PaymentSource
        fields = ('url', 'method', 'data', 'is_active')
    
    def validate_data(self, attrs, source):
        plugin = PaymentMethod.get_plugin(attrs['method'])
        serializer_class = plugin().get_serializer()
        serializer = serializer_class(data=attrs[source])
        if not serializer.is_valid():
            raise serializers.ValidationError(serializer.errors)
        return attrs
    
    def transform_data(self, obj, value):
        if not obj:
            return {}
        if obj.method:
            plugin = PaymentMethod.get_plugin(obj.method)
            serializer_class = plugin().get_serializer()
            return serializer_class().to_native(obj.data)
        return obj.data
    
    def metadata(self):
        meta = super(PaymentSourceSerializer, self).metadata()
        meta['data'] = {
            method.get_plugin_name(): method().get_serializer()().metadata()
                for method in PaymentMethod.get_plugins()
        }
        return meta


class TransactionSerializer(AccountSerializerMixin, serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Transaction
