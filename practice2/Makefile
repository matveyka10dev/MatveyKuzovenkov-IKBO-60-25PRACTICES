PYTHON ?= python3
ARGS ?= --help

.PHONY: run test

run:
	./run.sh $(ARGS)

test:
	$(PYTHON) -m unittest discover -s tests -t . -v
