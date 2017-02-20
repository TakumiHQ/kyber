import json

from functools import partial
from iso8601 import parse_date

from . import get_boto_client


def _list_images(project):
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


def _get_image_details(project, image_ids):
    batch_size = 100
    images = []
    client = get_boto_client('ecr', 'us-east-1')
    while len(image_ids) > 0:
        image_details = client.batch_get_image(
            repositoryName=project,
            imageIds=image_ids[:batch_size]
        )
        image_ids = image_ids[batch_size:]
        images += image_details['images']
    return images


def _get_creation_time(manifest):
    """ find the maximum `created` timestamp for the image described
    by this docker manifest
    """
    max_created = None
    for history in manifest['history']:
        parsed = json.loads(history['v1Compatibility'])
        created = parse_date(parsed['created'])
        if max_created is None or created > max_created:
            max_created = created
    return max_created


def get_image(project, tag):
    for image in _list_images(project):
        try:
            if image['imageTag'] == tag:
                return image
        except KeyError:
            pass  # untagged image, warn?


def list_images(project):
    return _list_images(project)


def get_image_details(project, image_ids):
    for image in _get_image_details(project, image_ids):
        manifest = json.loads(image['imageManifest'])
        yield dict(
            id=image['imageId'],
            created=_get_creation_time(manifest),
            manifest=manifest,
        )


def delete_images(project, image_ids):
    batch_size = 100
    images = []
    client = get_boto_client('ecr', 'us-east-1')
    while len(image_ids) > 0:
        client.batch_delete_image(
            repositoryName=project,
            imageIds=image_ids[:batch_size]
        )
        image_ids = image_ids[batch_size:]
