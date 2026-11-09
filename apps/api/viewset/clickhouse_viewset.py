from rest_framework import mixins, viewsets
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
        consumer_factory = ConsumerServiceFactory.get_service(serializer.validated_data['db_type'])
        if consumer_factory is None:
            return Response(
                {'success': False, 'message': f"Consumer service for {serializer.validated_data['db_type']} is not implemented."},
                status=400,
            )
        result, status = consumer_factory.create(
            database=serializer.validated_data['database'],
            tables=serializer.validated_data['tables'],
        )
        return Response(result, status=status)
