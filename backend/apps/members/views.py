from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import Member
from .serializers import MemberSerializer
import logging

logger = logging.getLogger(__name__)


@api_view(['GET'])
def get_members(request):
    """
    アクティブなメンバー一覧を取得

    GET /api/members/

    レスポンス:
    [
        {
            "id": 1,
            "name": "よんく",
            "is_active": true
        },
        ...
    ]
    """
    try:
        members = Member.objects.filter(is_active=True).order_by('name')
        serializer = MemberSerializer(members, many=True)
        return Response(serializer.data)
    except Exception as e:
        logger.error(f'get_members error: {e}', exc_info=True)
        return Response(
            {'detail': 'メンバー一覧の取得に失敗しました。'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
