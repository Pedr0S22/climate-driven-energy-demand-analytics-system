-- Criar extensões úteis (opcional)
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- 1. Tabela Principal de Utilizadores
CREATE TABLE users (
    id BIGSERIAL PRIMARY KEY,
    email TEXT NOT NULL UNIQUE,
    password VARCHAR(512) NOT NULL
);

-- 2. Perfis (Herança de Users)
CREATE TABLE client (
    users_id BIGINT PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE admin (
    users_id BIGINT PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE
);

-- 3. Pedidos
CREATE TABLE request (
    id BIGSERIAL PRIMARY KEY,
    date_req TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    users_id BIGINT NOT NULL REFERENCES users(id)
);

-- 4. Previsões (Relacionamento 1:1 com Request)
CREATE TABLE predictions_daily (
    request_id BIGINT PRIMARY KEY REFERENCES request(id) ON DELETE CASCADE,
    date_day DATE NOT NULL,
    value_pred FLOAT8 NOT NULL
);

CREATE TABLE predictions_hourly (
    request_id BIGINT PRIMARY KEY REFERENCES request(id) ON DELETE CASCADE,
    date_hour TIMESTAMP NOT NULL,
    value_pred FLOAT8 NOT NULL
);