from rest_framework import serializers
from .models import Order, Angle

class AngleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Angle
        fields = ['type', 'quantity']

class OrderSerializer(serializers.ModelSerializer):
    angles = AngleSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = [
            'id', 'user', 'created_on', 'is_gutter', 'colour_type',
            'ral_code', 'size', 'length_m', 'start_date', 'end_date',
            'total_price', 'angles'
        ]
        read_only_fields = ['user', 'created_on', 'total_price']