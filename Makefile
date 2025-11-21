.PHONY: format lint run

format:
	pipenv run black app/
	pipenv run ruff check --fix app/

lint:
	pipenv run black --check app/
	pipenv run ruff check app/

run:
	pipenv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
