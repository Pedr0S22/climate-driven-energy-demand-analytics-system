-- 02-insert-data.sql

CREATE EXTENSION IF NOT EXISTS pgcrypto;


WITH inserted_users AS (
    INSERT INTO users (email, password, username) 
    VALUES 
        ('pedro.silva@piacd.pt', crypt(:'pwd_admin', gen_salt('bf', 10)), 'pedro.silva'),
        ('diana.martins@piacd.pt', crypt(:'pwd_admin', gen_salt('bf', 10)), 'diana.martins'),
        ('beatriz.fernandes@piacd.pt', crypt(:'pwd_admin', gen_salt('bf', 10)), 'beatriz.fernandes'),
        ('ramyad.raadi@piacd.pt', crypt(:'pwd_admin', gen_salt('bf', 10)), 'ramyad.raadi'),
        ('francisca.mateus@piacd.pt', crypt(:'pwd_admin', gen_salt('bf', 10)), 'francisca.mateus'),
        ('nuno.seixas@piacd.pt', crypt(:'pwd_nuno', gen_salt('bf', 10)), 'nuno.seixas')
    RETURNING id
)
INSERT INTO admin (users_id)
SELECT id FROM inserted_users;