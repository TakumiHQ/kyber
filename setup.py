from setuptools import setup
from pip.req import parse_requirements
from pip.download import PipSession


def get_requirements():
    requirements = parse_requirements(
        os.path.join(os.path.dirname(__file__), "requirements.txt"),
        session=PipSession())
    return [str(req.req) for req in requirements]


setup(
    name='kyber',
    version='0.1',
    description='Deploy and manage simple apps in kubernetes.',
    install_requires=[str(req.req) for req in parse_requirements("requirements.txt", session=PipSession())],
    entry_points='''
        [console_scripts]
        kb=kyber:cli
    '''
)
