VENVDIR = .venv
VENV = ${VENVDIR}/bin/activate

venv:
	python3 -m venv ${VENVDIR}
	. ${VENV}; pip install sphinx build sphinx-autobuild

fclean:
	. ${VENV}; pip uninstall -y ulwazi
	rm -r ./dist | true
	rm -r ./ulwazi.egg-info | true
	rm -r ./docs/_build | true
	rm -r ${VENVDIR}

clean:
	. ${VENV}; pip uninstall -y ulwazi
	rm -r ./dist | true
	rm -r ./ulwazi.egg-info | true
	rm -r ./docs/_build | true

build: venv
	. ${VENV}; python3 -m build

install: build
	. ${VENV}; pip install dist/ulwazi-0.1.tar.gz

run: install
	. ${VENV}; cd docs && sphinx-autobuild . _build

rebuild: clean run
