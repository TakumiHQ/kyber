import os

from boto3.session import Session
from functools import partial


class Image(object):
    """ A broken-down representation of ecr/reponame:tag
    example:
        575449495505.dkr.ecr.us-east-1.amazonaws.com/takumi-server:git_12345
        region = us-east-1
        repo = takumi-server
        tag = git_12345
    """
    def __init__(self, image):
        self._image = image
        self.repo = self._repo_name(image)
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

    def __repr__(self):
        return "<ecr.Image region={} repo={} tag={} raw={}>".format(
            self.region, self.repo, self.tag, self._image)


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


def _list_images(repository, region):
    """ paginates through images in a repository, 50 at a time
    """
    client = get_boto_client('ecr', region)
    list_images = partial(client.list_images, maxResults=50)
    while True:
        resp = list_images(repositoryName=repository)
        for image in resp['imageIds']:
            yield image
        if 'nextToken' in resp:
            list_images = partial(list_images, nextToken=resp['nextToken'])
        else:
            break


def image_exists(image):
    ecr_image = Image(image)
    for image in _list_images(ecr_image.repo, ecr_image.region):
        try:
            if image['imageTag'] == ecr_image.tag:
                return True
        except KeyError:
            pass  # untagged image, warn?
    return False
