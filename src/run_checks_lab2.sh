docker compose -f docker-compose.testlocal.yml down -v

docker compose -f docker-compose.testlocal.yml up --build



docker compose -f docker-compose.test.yaml up --build --abort-on-container-exit --exit-code-from tests



docker compose -f docker-compose.test.yaml down -v --remove-orphans

docker compose -f docker-compose.test.yaml up -d --build adverts_db app_test



#allure generate ./allure-results -o ./allure-report --clean
#cp -r ./allure-report/history ./allure-results/history
#docker compose -f docker-compose.test.yaml run --rm --no-deps tests pytest -n 5 -v --alluredir=./allure-results


docker compose -f docker-compose.test.yaml run --rm --no-deps tests pytest -v --alluredir=./allure-results

allure generate ./allure-results -o ./allure-report --clean
allure open ./allure-report


docker compose -f docker-compose.test.yaml stop adverts_db


docker compose -f docker-compose.test.yaml up -d --wait adverts_db

#-----------------------------------------------------------------------

rm -rf ./allure-results/* && cp -r ./allure-report/history ./allure-results/history
docker compose -f docker-compose.test.yaml run --rm --no-deps tests pytest --alluredir=./allure-results

allure generate ./allure-results -o ./allure-report --clean

allure open ./allure-report




#---------------------------------------------------------

docker compose -f docker-compose.test.yaml run --rm --no-deps tests pytest -n 5 -v --alluredir=./allure-results



docker compose -f docker-compose.test.yaml run --rm tests pytest tests/integration tests/e2e -n 5 -v -s


docker compose -f docker-compose.test.yaml run --rm tests pytest tests/integration tests/e2e -n 5 -v -s

docker compose -f docker-compose.test.yaml run --rm tests pytest tests/e2e -n 5 --dist=worksteal -v

chmod +x run_e2e_curl.sh
./run_e2e_curl.sh


./run_e2e_curl.sh & ./run_e2e_curl.sh & ./run_e2e_curl.sh & ./run_e2e_curl.sh & ./run_e2e_curl.sh & wait

