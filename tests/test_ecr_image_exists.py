import mock
from kyber.lib.ecr import image_exists


def test_image_exists_returns_true_if_found():
    tag = 'test-tag'
    image = 'account.dkr.ecr.region.amazonaws.com/repo:{}'.format(tag)

    images = [{'imageTag': 'not it'}, {'imageTag': tag}]
    with mock.patch('kyber.lib.ecr._list_images', lambda *args: images):
        assert image_exists(image) is True


def test_image_exists_returns_false_if_not_found():
    tag = 'test-tag'
    image = 'account.dkr.ecr.region.amazonaws.com/repo:{}'.format(tag)

    images = [{'imageTag': 'not it'}, {'imageTag': 'also not it'}]
    with mock.patch('kyber.lib.ecr._list_images', lambda *args: images):
        assert image_exists(image) is False
