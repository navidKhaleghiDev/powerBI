from rest_framework import mixins, status, viewsets
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response

from apps.core.schema import consumer_viewset_schema
from apps.api.serializers import ConsumerSerializer
from apps.core.service.consumer_service import ConsumerServiceFactory


@consumer_viewset_schema
class ConsumerViewset(mixins.CreateModelMixin, viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated, IsAdminUser]
    serializer_class = ConsumerSerializer
    http_method_names = ['post', 'options']

    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data.copy()
        service = ConsumerServiceFactory.get_service(data.pop('db_type'))
        if service is None:
            return Response({
                'success': False,
                'database': data['database'],
                'tables': [],
                'message': 'Consumer creation is not implemented for this database type.',
            }, status=status.HTTP_400_BAD_REQUEST)
        result, response_status = service.create(topic=data['topic'], tables=data['tables'])
        return Response(result, status=response_status)
