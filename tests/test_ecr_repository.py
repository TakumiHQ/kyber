
from kyber.lib.ecr import Repository

dummy_image = '31337.dkr.ecr.is-mock-2.amazonaws.com/my-project:git_12345'


def test_repository_repo_name():
    assert Repository._repo_name(dummy_image) == 'my-project'


def test_repository_repo_tag():
    assert Repository._repo_tag(dummy_image) == 'git_12345'


def test_repository_repo_region():
    assert Repository._repo_region(dummy_image) == 'is-mock-2'
