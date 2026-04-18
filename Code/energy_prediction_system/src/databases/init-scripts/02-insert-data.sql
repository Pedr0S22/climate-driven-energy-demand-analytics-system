-- 02-insert-data.sql

CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Inserção em Massa de Administradores
WITH inserted_users AS (
    -- Adicionámos a coluna 'username' aqui em baixo
    INSERT INTO users (email, password, username) 
    VALUES 
        ('pedro.silva@piacd.pt', crypt('adoroSerAdmin123_', gen_salt('bf', 10)), 'pedro.silva'),
        ('diana.martins@piacd.pt', crypt('adoroSerAdmin123_', gen_salt('bf', 10)), 'diana.martins'),
        ('beatriz.fernandes@piacd.pt', crypt('adoroSerAdmin123_', gen_salt('bf', 10)), 'beatriz.fernandes'),
        ('ramyad.raadi@piacd.pt', crypt('adoroSerAdmin123_', gen_salt('bf', 10)), 'ramyad.raadi'),
        ('nuno.seixas@piacd.pt', crypt('piacd_2026_LIACD', gen_salt('bf', 10)), 'nuno.seixas')
    RETURNING id
)
INSERT INTO admin (users_id)
SELECT id FROM inserted_users;