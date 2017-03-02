from kyber.objects.environment import kube_from_template
from kyber.objects import App


def test_kube_from_template():
    app = App('test-app', 'ecr.testing.test/test-app', 'git_test', 31337)
    secret = kube_from_template('secret', app)
    assert secret is not None

    service = kube_from_template('service', app)
    assert service is not None

    deployment = kube_from_template('deployment', app)
    assert deployment is not None
