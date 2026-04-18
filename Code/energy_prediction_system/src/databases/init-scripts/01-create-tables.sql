-- 1. Limpeza das tabelas (útil para rodar o script várias vezes)
DROP TABLE IF EXISTS predictions_hourly CASCADE;
DROP TABLE IF EXISTS predictions_daily CASCADE;
DROP TABLE IF EXISTS request CASCADE;
DROP TABLE IF EXISTS admin CASCADE;
DROP TABLE IF EXISTS client CASCADE;
DROP TABLE IF EXISTS model CASCADE;
DROP TABLE IF EXISTS users CASCADE;

-- 2. Criação das Entidades Base
CREATE TABLE users (
    id                  BIGSERIAL,
    email               TEXT NOT NULL UNIQUE,          -- UNIQUE individual
    password            VARCHAR(512) NOT NULL,
    username            VARCHAR(512) NOT NULL UNIQUE,  -- UNIQUE individual
    account_regist_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    failed_login_att    INTEGER NOT NULL DEFAULT 0,
    acc_locked_until    TIMESTAMP,
    last_failed_att     TIMESTAMP,
    PRIMARY KEY(id)
);

CREATE TABLE model (
    model_name_id              BIGSERIAL,
    model_type                 VARCHAR(512) NOT NULL,
    model_creation_date        TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    model_server_relative_path VARCHAR(512) NOT NULL,
    rmse                       DOUBLE PRECISION NOT NULL,
    mae                        DOUBLE PRECISION NOT NULL,
    r2                         DOUBLE PRECISION NOT NULL,
    PRIMARY KEY(model_name_id)
);

-- 3. Criação das Entidades de Herança (Admin e Client)
CREATE TABLE client (
    users_id BIGINT,
    PRIMARY KEY(users_id),
    CONSTRAINT client_fk1 FOREIGN KEY (users_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE admin (
    users_id BIGINT,
    PRIMARY KEY(users_id),
    CONSTRAINT admin_fk1 FOREIGN KEY (users_id) REFERENCES users(id) ON DELETE CASCADE
);

-- 4. Tabela de Request (Relacionamento entre Users e Model)
CREATE TABLE request (
    id                  BIGSERIAL,
    date_req            TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    request_type	 VARCHAR(512) NOT NULL,
    model_model_name_id BIGINT NOT NULL,
    users_id            BIGINT NOT NULL,
    PRIMARY KEY(id),
    CONSTRAINT request_fk1 FOREIGN KEY (model_model_name_id) REFERENCES model(model_name_id) ON DELETE CASCADE,
    CONSTRAINT request_fk2 FOREIGN KEY (users_id) REFERENCES users(id) ON DELETE CASCADE
);

-- 5. Tabelas de Previsão (Com Chave Primária Composta para relação 1:N)
CREATE TABLE predictions_daily (
    request_id BIGINT,
    date_day   DATE NOT NULL,
    value_pred DOUBLE PRECISION NOT NULL,
    PRIMARY KEY(request_id, date_day), -- Chave composta permite várias previsões diárias para a mesma request
    CONSTRAINT predictions_daily_fk1 FOREIGN KEY (request_id) REFERENCES request(id) ON DELETE CASCADE
);

CREATE TABLE predictions_hourly (
    request_id BIGINT,
    date_hour  TIMESTAMP NOT NULL,
    value_pred DOUBLE PRECISION NOT NULL,
    PRIMARY KEY(request_id, date_hour), -- Chave composta permite várias previsões por hora para a mesma request
    CONSTRAINT predictions_hourly_fk1 FOREIGN KEY (request_id) REFERENCES request(id) ON DELETE CASCADE
);