.PHONY: run test clean rebuild debug logs

run:
	docker compose up --build --abort-on-container-exit

test:
	docker compose run --rm tests

clean:
	docker compose down -v

rebuild:
	docker compose down -v
	docker compose build --no-cache

debug:
	docker compose up --build

logs:
	docker compose logs -f