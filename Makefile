.PHONY: build up down

# Сборка проекта
build:
	docker compose --env-file local.env build

# Запуск сервиса
up:
	docker compose --env-file local.env up

# Cборка проекта и запуск сервисов
rebuild: build up

# Остановка сервиса
down:
	docker compose --env-file local.env down
