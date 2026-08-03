.PHONY: lint eval e2e test

lint:
	python3 scripts/lint.py

eval:
	python3 scripts/routing_eval.py

e2e:
	python3 scripts/e2e_eval.py

test: lint eval e2e
