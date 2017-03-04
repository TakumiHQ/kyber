import mock

from dulwich.errors import NotGitRepository

from kyber.init import get_default_name


def test_get_default_name_repo_name_if_repo_found():
    mock_repo = mock.Mock()
    mock_repo.get_config.return_value = {('remote', 'origin'): {'url': 'git@github.com:TakumiHQ/kyber.git'}}
    with mock.patch('kyber.init.git.Repo', return_value=mock_repo):
        assert get_default_name('/a/path/to/cool_repo') == 'kyber'


def test_get_default_name_current_directory_if_no_repo_found():
    with mock.patch('kyber.init.git.Repo', side_effect=NotGitRepository):
        assert get_default_name('/a/path/to/cool_repo') == 'cool_repo'
