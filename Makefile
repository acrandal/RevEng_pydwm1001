# Simple Makefile for how to operate module

all:
	@echo "No default target for build - see other targets (aka: test)"

test:
	pytest

doxygen_init:
	doxygen -g

doc:
	doxygen Doxyfile

clean:
	rm -rf docs

coverage:
	pytest --cov=. --cov-report=term-missing

black:
	black .