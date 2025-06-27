VENVDIR = .venv
VENV = ${VENVDIR}/bin/activate

venv:
	python3 -c "import venv" || \
        (echo "You must install python3-venv before you can build the documentation."; exit 1)
	@echo "... setting up virtualenv"
	python3 -m venv $(VENVDIR)
	. $(VENV); pip install --require-virtualenv \
	    --upgrade -r docs/requirements.txt \
		--log $(VENVDIR)/pip_install.log
	@test ! -f $(VENVDIR)/pip_list.txt || \
            mv $(VENVDIR)/pip_list.txt $(VENVDIR)/pip_list.txt.bak
	@. $(VENV); pip list --local --format=freeze > $(VENVDIR)/pip_list.txt
	@touch $(VENVDIR)

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
