test:
	tox

clean:
	find facepy/ tests/ -name "*.pyc" | xargs rm -rf

report: clean
	nosetests --with-cov --cov-config tests/coveragerc --cov-report term-missing --cover-erase --all-modules

release:
	python setup.py sdist register upload

documentation:
	cd docs; make html


.PHONY: flake8 pep8 syntax

flake8:
	@echo "flake8 syntax check"
# flake 8 --ignore=Warnings so we have to also use grep :(
	@flake8 --ignore=E501,W404 facepy/ tests/ | \
		(grep -vE 'W404' || true)

pep8:
	@echo "pep8 syntax check"
# We run pep8 on its own because flake8 embeds an old version of pep8
	@pep8 --ignore=E501 facepy/ tests/

syntax: flake8 pep8
