from types import SimpleNamespace
from unittest.mock import patch

import requests
from django.test import SimpleTestCase, override_settings
from rest_framework.test import APIRequestFactory, force_authenticate

from apps.api.viewset.connect_viewset import ConnectViewSet


@override_settings(KAFKA_CONNECT_URL="http://localhost:8083", KAFKA_CONNECT_TIMEOUT=10)
class ConnectListTests(SimpleTestCase):
    def request(self, admin=True):
        request = APIRequestFactory().get('/api/connect/')
        force_authenticate(request, user=SimpleNamespace(is_authenticated=True, is_staff=admin))
        return ConnectViewSet.as_view({'get': 'list'})(request)

    @patch('apps.core.service.connect_service.requests.get')
    def test_lists_names_and_empty_cluster(self, get):
        for names in (["orders", "customers"], []):
            get.return_value.json.return_value = names
            response = self.request()
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.data, names)
        get.assert_called_with('http://localhost:8083/connectors', headers={'Accept': 'application/json'}, timeout=10)

    @patch('apps.core.service.connect_service.requests.get')
    def test_invalid_upstream_response(self, get):
        for payload in ({}, [123]):
            get.return_value.json.return_value = payload
            self.assertEqual(self.request().status_code, 502)
        get.return_value.json.side_effect = ValueError('sensitive details')
        self.assertEqual(self.request().data, {'error': 'upstream_error'})

    @patch('apps.core.service.connect_service.requests.get')
    def test_network_and_http_failures(self, get):
        for error, expected in ((requests.Timeout('sensitive'), 503), (requests.ConnectionError('sensitive'), 503), (requests.HTTPError('sensitive'), 502)):
            get.side_effect = error
            response = self.request()
            self.assertEqual(response.status_code, expected)
            self.assertNotIn('sensitive', str(response.data))

    @patch('apps.core.service.connect_service.requests.get')
    def test_requires_administrator(self, get):
        self.assertEqual(self.request(admin=False).status_code, 403)
        get.assert_not_called()

    @override_settings(KAFKA_CONNECT_URL='')
    @patch('apps.core.service.connect_service.requests.get')
    def test_missing_configuration(self, get):
        self.assertEqual(self.request().status_code, 503)
        get.assert_not_called()


@override_settings(KAFKA_CONNECT_URL='http://localhost:8083', KAFKA_CONNECT_TIMEOUT=10)
class ConnectDetailTests(SimpleTestCase):
    def request(self, admin=True):
        request = APIRequestFactory().get('/api/connect/orders/')
        force_authenticate(request, user=SimpleNamespace(is_authenticated=True, is_staff=admin))
        return ConnectViewSet.as_view({'get': 'connector_config'})(request, source='orders')

    @patch('apps.core.service.connect_service.requests.get')
    def test_details_exclude_configuration(self, get):
        expected = {'connector.class': 'PostgresConnector', 'database.password': '[redacted]'}
        get.return_value.json.return_value = {**expected, 'database.password': 'secret'}
        response = self.request()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, expected)
        get.assert_called_once_with('http://localhost:8083/connectors/orders/config', headers={'Accept': 'application/json'}, timeout=10)

    @patch('apps.core.service.connect_service.requests.get')
    def test_failure_responses(self, get):
        from unittest.mock import Mock
        for error, code in ((requests.HTTPError(response=Mock(status_code=404)), 404), (requests.HTTPError(response=Mock(status_code=500)), 502), (requests.Timeout(), 503), (requests.ConnectionError(), 503), (ValueError(), 502)):
            get.side_effect = error
            self.assertEqual(self.request().status_code, code)

    @patch('apps.core.service.connect_service.requests.get')
    def test_invalid_payload(self, get):
        for payload in ([], {'tasks': [None]}, {'port': 5432}):
            get.return_value.json.return_value = payload
            self.assertEqual(self.request().status_code, 502)

    @patch('apps.core.service.connect_service.requests.get')
    def test_permissions(self, get):
        self.assertEqual(self.request(admin=False).status_code, 403)
        get.assert_not_called()

    @override_settings(KAFKA_CONNECT_URL='')
    @patch('apps.core.service.connect_service.requests.get')
    def test_not_configured(self, get):
        self.assertEqual(self.request().status_code, 503)
        get.assert_not_called()
