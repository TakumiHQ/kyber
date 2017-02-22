
from kyber.lib.ecr import Image

dummy_image = '31337.dkr.ecr.is-mock-2.amazonaws.com/my-project:git_12345'


def test_image_repo_name():
    assert Image._repo_name(dummy_image) == 'my-project'


def test_image_repo_tag():
    assert Image._repo_tag(dummy_image) == 'git_12345'


def test_image_repo_region():
    assert Image._repo_region(dummy_image) == 'is-mock-2'


def test_image():
    image = Image(dummy_image)
    assert image.repo == 'my-project'
    assert image.tag == 'git_12345'
    assert image.region == 'is-mock-2'
