.PHONY: setup

setup: venv
	venv/bin/python setup.py develop
	venv/bin/pip install -r test-requirements.txt

venv:
	virtualenv venv

clean:
	rm -rf venv
	rm -rf *.egg-info
	rm *.pyc


test:
	venv/bin/py.test tests/ -vsx --pdb
