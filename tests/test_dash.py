import mock
from collections import namedtuple

from kyber.context import ContextError
from kyber.dash import launch


KubeConfig = namedtuple('KubeConfig', 'cluster user')


def test_launch_calls_service_dashboard():
    with mock.patch('kyber.dash.Context'):
        with mock.patch('kyber.dash.service_dashboard') as mock_service_dashboard:
            launch(cfg=mock.MagicMock(), executor=mock.Mock())
            assert mock_service_dashboard.called


def test_launch_calls_namespace_dashboard_if_context_error():
    with mock.patch('kyber.dash.Context') as mock_context:
        mock_context.side_effect = ContextError('meh')
        with mock.patch('kyber.dash.service_dashboard') as mock_service_dashboard:
            with mock.patch('kyber.dash.namespace_dashboard') as mock_namespace_dashboard:
                launch(cfg=mock.MagicMock(), executor=mock.Mock())
                assert not mock_service_dashboard.called
                assert mock_namespace_dashboard.called
