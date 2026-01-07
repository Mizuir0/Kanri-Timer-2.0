from rest_framework import serializers
from .models import Member


class MemberSerializer(serializers.ModelSerializer):
    """メンバーシリアライザー"""

    class Meta:
        model = Member
        fields = ('id', 'name', 'is_active')
        read_only_fields = ('id',)
