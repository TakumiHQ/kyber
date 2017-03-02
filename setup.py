from setuptools import setup, find_packages
import fastentrypoints
from pip.req import parse_requirements
from pip.download import PipSession


def get_requirements():
    requirements = parse_requirements(
        os.path.join(os.path.dirname(__file__), "requirements.txt"),
        session=PipSession())
    return [str(req.req) for req in requirements]


def get_version():
    __version__ = None
    with open('kyber/_version.py') as version_src:
        exec(version_src.read())
    return __version__

setup(
    name='kyber-k8s',
    version=get_version(),
    description='Deploy and manage simple apps in kubernetes.',
    url='https://github.com/TakumiHQ/kyber',
    author='Steinn Eldjarn Sigurdarson',
    author_email='steinn@takumi.com',
    keywords=['aws', 'kubernetes', 'deployments', 'app', 'paas'],
    install_requires=[str(req.req) for req in parse_requirements("requirements.txt", session=PipSession())],
    packages=find_packages(),
    package_data={'kyber': ['templates/*.yaml', 'templates/*.sh']},
    entry_points='''
        [console_scripts]
        kb=kyber:cli
    '''
)
