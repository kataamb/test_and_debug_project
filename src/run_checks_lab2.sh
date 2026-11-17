docker compose -f docker-compose.testlocal.yml down -v

docker compose -f docker-compose.testlocal.yml up --build

docker compose -f docker-compose.test.yaml up --build --abort-on-container-exit --exit-code-from tests

docker compose -f docker-compose.test.yaml down -v --remove-orphans

docker compose -f docker-compose.test.yaml up -d --build adverts_db app_test


docker compose -f docker-compose.test.yaml run --rm tests pytest tests/integration tests/e2e -n 5 -v -s


docker compose -f docker-compose.test.yaml run --rm tests pytest tests/integration tests/e2e -n 5 -v -s

docker compose -f docker-compose.test.yaml run --rm tests pytest tests/e2e -n 5 --dist=worksteal -v

