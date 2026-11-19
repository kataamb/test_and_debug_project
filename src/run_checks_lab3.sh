docker compose -f docker-compose.testlocal.yml down -v

docker compose -f docker-compose.testlocal.yml up --build



#docker compose up --build
#docker compose down -v



cd benchmark

# 1. Прогон чистого SQL
docker compose run --rm bench_runner python benchmark/run_bench.py --impl sql

# 2. Прогон ORM (в новом чистом контейнере)
docker compose run --rm bench_runner python benchmark/run_bench.py --impl orm


#