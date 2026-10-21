PYTHON ?= python3

.PHONY: run test

run:
	./run.sh

test:
	$(PYTHON) -m unittest discover -s tests -t . -v
