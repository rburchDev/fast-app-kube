venv/bin/activate: requirements.txt
	python3 -m venv venv
	./venv/bin/pip install -r requirements.txt

venv/bin/activate-test: requirements-test.txt
	python3 -m venv venv
	./venv/bin/pip install -r requirements-test.txt

black-check:
	./venv/bin/black --check .

lint:
	./venv/bin/pylint src/services src/worker src/logger.py

clean:
	rm -rf __pycache__
	rm -rf venv