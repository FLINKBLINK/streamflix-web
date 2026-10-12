-- Execute uma única vez no banco streaming_db já existente antes de publicar esta versão.
-- Amplia o campo para suportar hashes Argon2 e adiciona papel de autorização.
ALTER TABLE usuario
    MODIFY COLUMN senha_hash VARCHAR(255) NOT NULL
    COMMENT 'Hash de senha Argon2; hashes SHA-256 antigos podem ser migrados no próximo login';

ALTER TABLE usuario
    ADD COLUMN papel ENUM('USUARIO','ADMIN') NOT NULL DEFAULT 'USUARIO'
    AFTER senha_hash;

-- Opcional: após escolher a conta que será administradora, execute manualmente:
-- UPDATE usuario SET papel = 'ADMIN' WHERE email = 'seu-email@exemplo.com';
