start_server:
	uvicorn app.main:app --reload

build:
	docker compose up -d

build_without_orphans:
	docker compose up --build -d --remove-orphans

stop:
	docker compose down

show_logs:
	docker compose logs