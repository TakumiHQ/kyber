import json
import os

from boto3.session import Session
from functools import partial


class Repository(object):
    """ A broken-down representation of ecr/reponame:tag
    example:
        575449495505.dkr.ecr.us-east-1.amazonaws.com/takumi-server:git_12345
        region = us-east-1
        name = takumi-server
        tag = git_12345
    """
    def __init__(self, image):
        self.name = self._repo_name(image)
        self.tag = self._repo_tag(image)
        self.region = self._repo_region(image)

    @staticmethod
    def _repo_name(image):
        name = image.split("/")[1]
        if ":" in name:
            name = name.split(":")[0]
        return name

    @staticmethod
    def _repo_tag(image):
        tag = image.split(":")[1]
        return tag

    @staticmethod
    def _repo_region(image):
        host = image.split("/")[0]
        account, _, _, region, _ = host.split(".", 4)
        return region


def get_boto_client(service, region='eu-west-1'):
    kwargs = {}
    access_key_id = os.environ.get('AWS_ACCESS_KEY_ID')
    secret_access_key = os.environ.get('AWS_SECRET_ACCESS_KEY')
    kwargs['region_name'] = region

    if access_key_id is not None:
        kwargs['aws_access_key_id'] = access_key_id

    if secret_access_key is not None:
        kwargs['aws_secret_access_key'] = secret_access_key

    session = Session(**kwargs)
    return session.client(service)


def _list_images(repository):
    """ paginates through images in a repository, 50 at a time
    """
    client = get_boto_client('ecr', 'us-east-1')
    list_images = partial(client.list_images, maxResults=50)
    while True:
        resp = list_images(repositoryName=project)
        for image in resp['imageIds']:
            yield image
        if 'nextToken' in resp:
            list_images = partial(list_images, nextToken=resp['nextToken'])
        else:
            break


def docker_exists(app):
    repository = Repository(app.image)
    image = get_image(repository.name)
    return image is not None

def get_image(project, tag):
    for image in _list_images(project):
        try:
            if image['imageTag'] == tag:
                return image
        except KeyError:
            pass  # untagged image, warn?
