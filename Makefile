run:
	pipenv shell \
	uvicorn app.main:app --reload

start_server:
	uvicorn app.main:app --reload

build:
	docker compose up -d

stop:
	docker compose down