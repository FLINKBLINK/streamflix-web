# Dicionário de dados

O esquema completo está em `database/schema.sql`. As tabelas abaixo são as principais para as análises.

| Tabela | Finalidade | Chave/relacionamentos relevantes |
|---|---|---|
| `usuario` | Dados cadastrais demonstrativos | PK `id_usuario` |
| `plano` | Planos e preço mensal | PK `id_plano` |
| `assinatura` | Plano contratado e status | FK para `usuario` e `plano` |
| `perfil` | Perfis associados a cada usuário | FK para `usuario` |
| `conteudo` | Filmes e séries do catálogo | PK `id_conteudo` |
| `genero` | Catálogo de gêneros | PK `id_genero` |
| `conteudo_genero` | Relação N:N entre conteúdo e gênero | PK composta e FKs |
| `episodio` | Episódios de séries | FK para `conteudo` |
| `historico_visualizacao` | Registros de reprodução | FK para `perfil`, `conteudo` e, opcionalmente, `episodio` |

## Campos analíticos

- `historico_visualizacao.data_hora_inicio`: data e hora de início da reprodução.
- `historico_visualizacao.tempo_assistido_min`: minutos assistidos registrados.
- `historico_visualizacao.concluido`: indicador booleano de conclusão.
- `conteudo.tipo`: tipo do conteúdo (`FILME` ou `SERIE`).
- `assinatura.status`: status contratual; a receita estimada considera apenas `ATIVA`.
- `plano.preco_mensal`: preço mensal cadastrado para o plano.

Os registros de demonstração são fictícios. A estrutura não representa eventos de cobrança ou pagamentos efetivamente processados.
