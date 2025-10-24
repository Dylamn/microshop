up:
	docker compose up -d

watch:
	docker compose up --build --watch

down:
	docker compose down

build:
	docker compose build

logs:
	docker compose logs -f $(s)
