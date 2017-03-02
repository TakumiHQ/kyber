import mock
from collections import namedtuple

from kyber.context import ContextError
from kyber.dash import launch, _kube_dash_base_url


KubeConfig = namedtuple('KubeConfig', 'cluster user')


def test_kube_dash_base_url_adds_auth_if_found():
    cfg = KubeConfig(cluster=dict(server='https://test'), user=dict(username='mocky', password='python'))
    url = _kube_dash_base_url(cfg)
    assert url.netloc == 'mocky:python@test'


def test_kube_dash_base_url_adds_no_auth_if_not_found():
    cfg = KubeConfig(cluster=dict(server='https://test'), user=dict())
    url = _kube_dash_base_url(cfg)
    assert url.netloc == 'test'


def test_launch_calls_service_dashboard():
    with mock.patch('kyber.dash.Context'):
        with mock.patch('kyber.dash.service_dashboard') as mock_service_dashboard:
            launch(cfg=mock.Mock(), executor=mock.Mock())
            assert mock_service_dashboard.called


def test_launch_calls_namespace_dashboard_if_context_error():
    with mock.patch('kyber.dash.Context') as mock_context:
        mock_context.side_effect = ContextError('meh')
        with mock.patch('kyber.dash.service_dashboard') as mock_service_dashboard:
            with mock.patch('kyber.dash.namespace_dashboard') as mock_namespace_dashboard:
                launch(cfg=mock.Mock(), executor=mock.Mock())
                assert not mock_service_dashboard.called
                assert mock_namespace_dashboard.called


def test_launch_echos_url_if_executor_not_found():
    with mock.patch('kyber.dash.Context'):
        with mock.patch('kyber.dash.service_dashboard'):
            with mock.patch('kyber.dash.namespace_dashboard'):
                with mock.patch('kyber.dash.click') as mock_click:
                    mock_exec = mock.Mock(side_effect=Exception('mocky pythons holy exception'))
                    launch(cfg=mock.Mock(), executor=mock_exec)
                    assert mock_exec.called
                    assert mock_click.echo.called
                    assert 'mocky pythons holy exception' in mock_click.echo.call_args_list[1][0][0]
                    assert 'URL: ' in mock_click.echo.call_args_list[2][0][0]
