#!/usr/bin/env bash
set -e

BASE_URL="http://localhost:8001"
CONTAINER_NAME="adverts_db_tests_container"

# Уникальные идентификаторы конкретно для этого запуска
RAND_ID=$(python3 -c "import uuid; print(uuid.uuid4().hex[:8])")
WORKER_HEADER="X-Worker-ID: worker_${RAND_ID}"
CATEGORY_ID=$(python3 -c "import uuid; print(uuid.uuid4())")
BG_SELLER_ID=$(python3 -c "import uuid; print(uuid.uuid4())")
BG_ADVERT_ID=$(python3 -c "import uuid; print(uuid.uuid4())")
USER_UUID=$(python3 -c "import uuid; print(uuid.uuid4())")

EMAIL="curl_${RAND_ID}@example.com"
USERNAME="user_${RAND_ID}"
PASSWORD="SecurePassword123!"

# Аналог try ... finally: очистка данных ЭТОГО запуска при любом завершении скрипта
cleanup() {
  echo "=== Очистка тестовых данных запуска ($RAND_ID) ==="
  docker exec -i "$CONTAINER_NAME" psql -U postgres -d adverts_db >/dev/null <<EOF
DELETE FROM adv_uuid.adverts WHERE id_category = '$CATEGORY_ID';
DELETE FROM adv_uuid.sellers WHERE profile_id IN ('$USER_UUID', '$BG_SELLER_ID');
DELETE FROM adv_uuid.profiles WHERE id IN ('$USER_UUID', '$BG_SELLER_ID');
DELETE FROM adv_uuid.categories WHERE id = '$CATEGORY_ID';
EOF
}
trap cleanup EXIT

echo "=== 0. Подготовка фоновых данных для запуска ($RAND_ID) ==="
docker exec -i "$CONTAINER_NAME" psql -U postgres -d adverts_db >/dev/null <<EOF
INSERT INTO adv_uuid.categories (id, name) VALUES ('$CATEGORY_ID', 'Cat_$RAND_ID');
INSERT INTO adv_uuid.profiles (id, nickname, fio, email, phone_number, password)
  VALUES ('$BG_SELLER_ID', 'seller_$RAND_ID', 'Фоновый Продавец', 'bg_$RAND_ID@example.com', '+79990001122', 'pwd');
INSERT INTO adv_uuid.sellers (id, profile_id, rating) VALUES ('$BG_SELLER_ID', '$BG_SELLER_ID', 5);
INSERT INTO adv_uuid.adverts (id, content, description, price, id_category, id_seller)
  VALUES ('$BG_ADVERT_ID', 'Витринный товар ($RAND_ID)', 'Описание', 15000, '$CATEGORY_ID', '$BG_SELLER_ID');
EOF

echo "=== 1. Регистрация пользователя ($EMAIL) ==="
curl -s -X POST "${BASE_URL}/api/v1/users/register" \
  -H "${WORKER_HEADER}" \
  -H "Content-Type: application/json" \
  -d "{
    \"id\": \"${USER_UUID}\",
    \"username\": \"${USERNAME}\",
    \"email\": \"${EMAIL}\",
    \"full_name\": \"Curl User ${RAND_ID}\",
    \"phone\": \"+79991234567\",
    \"password\": \"${PASSWORD}\",
    \"rep_password\": \"${PASSWORD}\"
  }"
echo -e "\n"

echo "=== 2. Логин и получение JWT токена ==="
LOGIN_RESP=$(curl -s -X POST "${BASE_URL}/api/v1/users/login" \
  -H "${WORKER_HEADER}" \
  -H "Content-Type: application/json" \
  -d "{
    \"email\": \"${EMAIL}\",
    \"password\": \"${PASSWORD}\"
  }")
TOKEN=$(echo "$LOGIN_RESP" | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")
echo -e "Токен получен.\n"

echo "=== 3. Просмотр всех объявлений на витрине ==="
curl -s -X GET "${BASE_URL}/api/v2/adverts/" \
  -H "${WORKER_HEADER}" \
  -H "Authorization: Bearer ${TOKEN}"
echo -e "\n"

echo "=== 4. Создание первого объявления ==="
FIRST_RESP=$(curl -s -X POST "${BASE_URL}/api/v2/adverts/" \
  -H "${WORKER_HEADER}" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d "{
    \"content\": \"Наушники ($RAND_ID)\",
    \"description\": \"Беспроводные\",
    \"price\": 5500,
    \"id_category\": \"${CATEGORY_ID}\"
  }")
echo "$FIRST_RESP"
FIRST_ID=$(echo "$FIRST_RESP" | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])")
echo -e "\n"

echo "=== 5. Создание второго объявления ==="
curl -s -X POST "${BASE_URL}/api/v2/adverts/" \
  -H "${WORKER_HEADER}" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d "{
    \"content\": \"Монитор ($RAND_ID)\",
    \"description\": \"144 Гц\",
    \"price\": 24000,
    \"id_category\": \"${CATEGORY_ID}\"
  }"
echo -e "\n"

echo "=== 6. Получение списка своих объявлений (ожидаем 2) ==="
curl -s -X GET "${BASE_URL}/api/v2/adverts/created" \
  -H "${WORKER_HEADER}" \
  -H "Authorization: Bearer ${TOKEN}"
echo -e "\n"

echo "=== 7. Удаление первого объявления (${FIRST_ID}) ==="
curl -i -s -X DELETE "${BASE_URL}/api/v2/adverts/${FIRST_ID}" \
  -H "${WORKER_HEADER}" \
  -H "Authorization: Bearer ${TOKEN}"
echo -e "\n"


