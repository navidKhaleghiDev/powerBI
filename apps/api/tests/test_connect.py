from types import SimpleNamespace
from unittest.mock import Mock, patch

import requests
from django.test import SimpleTestCase, override_settings
from rest_framework.test import APIRequestFactory, force_authenticate

from apps.api.viewset.connect_viewset import ConnectViewSet


@override_settings(KAFKA_CONNECT_URL="http://connect:8083", KAFKA_CONNECT_TIMEOUT=10)
class ConnectCreateTests(SimpleTestCase):
    def setUp(self):
        self.payload = {
            "name": "orders", "db_type": "postgresql", "config": { "database.hostname": "postgres",
            "database.user": "replicator", "database.password": " secret ",
            "database.dbname": "bi", "topic.prefix": "bi",
            "slot.name": "orders", "publication.name": "orders",
            "table.include.list": "public.orders",
            },
        }

    def request(self, payload=None, admin=True):
        request = APIRequestFactory().post('/api/connect/', payload or self.payload, format='json')
        force_authenticate(request, user=SimpleNamespace(is_authenticated=True, is_staff=admin))
        return ConnectViewSet.as_view({'post': 'create'})(request)

    @patch('apps.core.service.connect_service.requests.post')
    def test_create_forwards_config_without_exposing_credentials(self, post):
        post.return_value = Mock(status_code=201)
        response = self.request()
        self.assertEqual(response.status_code, 201)
        forwarded = post.call_args.kwargs['json']
        self.assertEqual(forwarded['name'], 'orders')
        self.assertNotIn('name', forwarded['config'])
        self.assertEqual(forwarded['config']['database.password'], ' secret ')
        self.assertEqual(forwarded['config']['database.port'], '5432')
        self.assertEqual(forwarded['config']['topic.prefix'], 'bi')
        self.assertNotIn('password', str(response.data))
        self.assertEqual(post.call_args.args[0], 'http://connect:8083/connectors')
        self.assertEqual(post.call_args.kwargs['timeout'], 10)

    @patch('apps.core.service.connect_service.requests.post')
    def test_invalid_port_rejected_before_upstream_request(self, post):
        response = self.request({**self.payload, 'config': {**self.payload['config'], 'database.port': 0}})
        self.assertEqual(response.status_code, 400)
        post.assert_not_called()

    @patch('apps.core.service.connect_service.requests.post')
    def test_upstream_failure_is_sanitized(self, post):
        for code, expected in [(400, 400), (409, 409), (500, 502)]:
            post.return_value.raise_for_status.side_effect = requests.HTTPError(
                'sensitive upstream details', response=Mock(status_code=code),
            )
            response = self.request()
            self.assertEqual(response.status_code, expected)
            self.assertNotIn('sensitive', str(response.data))
        post.side_effect = requests.Timeout('sensitive timeout')
        self.assertEqual(self.request().status_code, 503)

    @patch('apps.core.service.connect_service.requests.post')
    def test_requires_administrator(self, post):
        self.assertEqual(self.request(admin=False).status_code, 403)
        post.assert_not_called()

    @override_settings(KAFKA_CONNECT_URL='')
    @patch('apps.core.service.connect_service.requests.post')
    def test_missing_configuration(self, post):
        self.assertEqual(self.request().status_code, 503)
        post.assert_not_called()
