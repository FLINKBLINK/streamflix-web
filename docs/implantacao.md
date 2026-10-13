# Implantação e operação

## 1. Banco novo

Use esta sequência somente em um banco vazio criado para o StreamFlix Web:

1. Crie o banco `streaming_db`.
2. Execute `database/schema.sql`.
3. Execute `database/seed.sql` uma única vez.
4. Configure `DATABASE_URL` no ambiente da aplicação.

O arquivo `seed.sql` contém dados fictícios. Os usuários semeados têm um hash reservado para demonstração e não conseguem entrar pela tela de login.

## 2. Banco já existente

Antes de qualquer alteração, faça um backup e confira o esquema atual. **Não execute `schema.sql` sobre um banco existente**: ele cria tabelas e não é uma migração incremental.

A migração `database/migrations/001_authentication.sql` destina-se a uma base anterior em que a tabela `usuario` já existe, `senha_hash` está presente e a coluna `papel` ainda não existe. Ela altera `senha_hash` para comportar hashes Argon2 e adiciona o papel padrão `USUARIO`.

Antes de executá-la, verifique a existência da coluna:

```sql
SELECT COLUMN_NAME, COLUMN_TYPE
FROM information_schema.COLUMNS
WHERE TABLE_SCHEMA = DATABASE()
  AND TABLE_NAME = 'usuario'
  AND COLUMN_NAME IN ('senha_hash', 'papel');
```

- Se `papel` já existir, **não execute a migração novamente**.
- Se `papel` não existir e a base corresponder às condições acima, execute a migração uma única vez.
- Se a estrutura for diferente, faça uma migração específica após backup; não tente adaptar executando comandos repetidos às cegas.

Depois, confirme os valores:

```sql
SHOW COLUMNS FROM usuario LIKE 'papel';
SELECT papel, COUNT(*) AS total FROM usuario GROUP BY papel;
```

## 3. Primeiro administrador

O cadastro pela interface sempre cria uma conta com papel `USUARIO`; não existe cadastro público de administradores.

1. Inicie a aplicação com o banco configurado.
2. Registre a conta que deverá administrar o sistema.
3. No MySQL, confirme o endereço e altere apenas a conta escolhida:

```sql
SELECT id_usuario, nome, email, papel
FROM usuario
WHERE email = 'seu-email@exemplo.com';

UPDATE usuario
SET papel = 'ADMIN'
WHERE email = 'seu-email@exemplo.com';

SELECT ROW_COUNT() AS linhas_alteradas;
```

Confira que a atualização afetou exatamente uma linha. Saia e entre novamente para renovar a sessão. Nunca promova contas de demonstração ou usuários não verificados.

## 4. Variáveis de ambiente

Obrigatórias:
- `DATABASE_URL`: URL SQLAlchemy para o banco MySQL.
- `SESSION_SECRET`: chave aleatória forte, obrigatória em produção.

O `render.yaml` solicita ao Render que gere `SESSION_SECRET` automaticamente. Após criar ou sincronizar o serviço, confirme no painel que a variável existe e é secreta. Para gerar uma chave manualmente:

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Opcionais:
- `APP_ENV=production`: identifica explicitamente o ambiente de produção.
- `CORS_ORIGINS`: origens separadas por vírgula, apenas se o frontend estiver em outro domínio.
- Certificado CA do banco, caso exigido pelo provedor. O código de conexão atual procura o certificado Aiven em `/etc/secrets/ca.pem`.

Não coloque segredos no repositório, em logs ou em documentação pública.

## 5. Verificação após deploy

1. Confirme que o serviço inicia sem erro de configuração.
2. Acesse `/api/health`; o resultado esperado é HTTP 200 com banco conectado.
3. Teste cadastro, login, logout e token CSRF.
4. Confirme que um usuário comum não acessa endpoints administrativos e que o histórico de um usuário não expõe dados de outro.
5. Entre com a conta administrativa configurada e valide dashboard e analytics.
6. Confira os logs do serviço e do workflow de testes.

O health check testa a conectividade com o banco, mas não substitui testes funcionais ou de segurança.

## 6. Testes de integração MySQL

Os testes padrão usam SQLite em memória. Para o teste adicional de integração, defina `TEST_DATABASE_URL` apontando para um banco MySQL separado e descartável. O teste confere tabelas essenciais e funções SQL específicas do MySQL. Nunca use a URL do banco de produção para executar testes.

O limitador de login mantém contadores em memória por processo. Se o serviço tiver múltiplos workers ou instâncias, configure também rate limiting compartilhado no proxy/WAF ou use armazenamento compartilhado.
