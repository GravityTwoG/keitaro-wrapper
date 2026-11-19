.PHONY: up down logs ps backend-test backend-lint frontend-check e2e migrate

up:
	docker compose up -d --build --wait

down:
	docker compose down -v --remove-orphans

logs:
	docker compose logs -f --tail=100

ps:
	docker compose ps

migrate:
	cd backend && uv run alembic upgrade head

backend-test:
	cd backend && uv run pytest

backend-lint:
	cd backend && uv run ruff check . && uv run ruff format --check .

frontend-check:
	npm --prefix frontend run format:check
	npm --prefix frontend run lint
	npm --prefix frontend run typecheck
	npm --prefix frontend run knip
	npm --prefix frontend run build

e2e:
	npm run test:e2e
