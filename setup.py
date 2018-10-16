from setuptools import setup, find_packages
import os
import fastentrypoints


def parse_requirements(filename):
    reqs = []
    with open(filename) as f:
        for req in f.readlines():
            if req.startswith("#"):
                continue
            reqs.append(req.replace("\n", ""))
    return reqs


def get_requirements():
    requirements = parse_requirements(os.path.join(os.path.dirname(__file__), "requirements.txt"))
    return [str(req) for req in requirements]


def get_version():
    __version__ = None
    with open('kyber/_version.py') as version_src:
        exec(version_src.read())
    return __version__


if __name__ == "__main__":
    install_requires = get_requirements()
    dependency_links = []

    for req in install_requires:
        if req.startswith("-e"):
            dependency_links.append(req.replace("-e ", ""))
            install_requires.remove(req)
    # pykube requirements
    install_requires += [ "requests>=2.12",
        "PyYAML",
        "six>=1.10.0",
        "tzlocal",
    ]

    setup(
        name='kyber-k8s',
        version=get_version(),
        description='Deploy and manage simple apps in kubernetes.',
        url='https://github.com/TakumiHQ/kyber',
        author='Steinn Eldjarn Sigurdarson',
        author_email='steinn@takumi.com',
        keywords=['aws', 'kubernetes', 'deployments', 'app', 'paas'],
        install_requires=install_requires,
        dependency_links=dependency_links,
        packages=find_packages(),
        package_data={'kyber': ['templates/*.yaml', 'templates/*.sh']},
        entry_points='''
            [console_scripts]
            kb=kyber:cli
        '''
    )
