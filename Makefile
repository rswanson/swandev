.PHONY: lint eval

lint:
	python3 scripts/lint.py

eval:
	python3 scripts/routing_eval.py
