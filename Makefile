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

test:
	docker compose --profile testing run --rm test-$(s) pytest $(args)

test\:cov:
	docker compose --profile testing run --rm test-$(s) pytest --cov --cov-report=html $(args)

debug:
	docker compose exec -it $(s) bash

migrate\:upgrade:
	docker compose exec $(s) alembic upgrade head

migrate\:downgrade:
	docker compose exec $(s) alembic downgrade head-$(n)
