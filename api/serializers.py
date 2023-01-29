from rest_framework import serializers
from .models import Quote


class QuoteSerializer(serializers.ModelSerializer):
    cost = serializers.SerializerMethodField('get_cost')
    class Meta:
        model = Quote
        fields = ['customer_name', 'description', 'state', 'coverage_type', 'cost']


    def get_cost(self, obj: Quote):
        rate = obj.rate
        return dict(
            subtotal=rate.subtotal,
            taxes=rate.taxes,
            total=rate.total
        )