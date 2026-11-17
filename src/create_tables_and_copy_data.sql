-- Очищаем схему перед запуском
DROP SCHEMA IF EXISTS adv_uuid CASCADE;
CREATE SCHEMA adv_uuid;

-- Включаем расширение для UUID
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Таблица profiles
CREATE TABLE adv_uuid.profiles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    nickname VARCHAR(50) NOT NULL UNIQUE,
    fio VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    phone_number VARCHAR(20),
    password VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица categories
CREATE TABLE adv_uuid.categories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(50) NOT NULL UNIQUE
);

-- Таблица customers
CREATE TABLE adv_uuid.customers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    profile_id UUID NOT NULL REFERENCES adv_uuid.profiles(id) ON DELETE CASCADE,
    rating INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица sellers
CREATE TABLE adv_uuid.sellers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    profile_id UUID NOT NULL REFERENCES adv_uuid.profiles(id) ON DELETE CASCADE,
    rating INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица adverts
CREATE TABLE adv_uuid.adverts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    content TEXT NOT NULL,
    description TEXT,
    id_category UUID NOT NULL REFERENCES adv_uuid.categories(id) ON DELETE CASCADE,
    price INTEGER NOT NULL CHECK (price >= 0),
    id_seller UUID NOT NULL REFERENCES adv_uuid.sellers(id) ON DELETE CASCADE,
    date_created TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица deals
CREATE TABLE adv_uuid.deals (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    id_advert UUID NOT NULL REFERENCES adv_uuid.adverts(id) ON DELETE CASCADE,
    id_customer UUID NOT NULL REFERENCES adv_uuid.customers(id) ON DELETE CASCADE,
    date_created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    address TEXT NOT NULL
);

-- Таблица likes
CREATE TABLE adv_uuid.likes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    id_customer UUID NOT NULL REFERENCES adv_uuid.customers(id) ON DELETE CASCADE,
    id_advert UUID NOT NULL REFERENCES adv_uuid.adverts(id) ON DELETE CASCADE,
    date_created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (id_customer, id_advert)
);

