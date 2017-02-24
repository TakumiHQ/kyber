.PHONY: setup

setup: venv
	venv/bin/python setup.py develop
	venv/bin/pip install -r test-requirements.txt

venv:
	virtualenv venv

clean:
	rm -rf dist build kyber.egg-info

test:
	venv/bin/py.test tests/ -vsx --pdb

release:
	venv/bin/python setup.py sdist bdist_wheel
	twine upload dist/*.tar.gz
	twine upload dist/*.whl

release_test:
	venv/bin/python setup.py sdist bdist_wheel upload -r pypitest
