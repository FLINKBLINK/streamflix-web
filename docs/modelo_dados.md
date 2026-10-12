# Modelo de dados

O banco utiliza relacionamentos relacionais com chaves primárias e estrangeiras. O diagrama abaixo resume os relacionamentos centrais definidos em `database/schema.sql`.

```mermaid
erDiagram
    USUARIO ||--o{ PERFIL : possui
    USUARIO ||--o{ ASSINATURA : contrata
    PLANO ||--o{ ASSINATURA : define
    PERFIL ||--o{ HISTORICO_VISUALIZACAO : registra
    CONTEUDO ||--o{ HISTORICO_VISUALIZACAO : recebe
    CONTEUDO ||--o{ EPISODIO : contem
    EPISODIO o|--o{ HISTORICO_VISUALIZACAO : referencia
    CONTEUDO ||--o{ CONTEUDO_GENERO : classificado
    GENERO ||--o{ CONTEUDO_GENERO : classifica

    USUARIO {
        int id_usuario PK
        varchar nome
        varchar email UK
        char pais
    }
    PERFIL {
        int id_perfil PK
        int id_usuario FK
        varchar nome_perfil
        boolean perfil_infantil
    }
    ASSINATURA {
        int id_assinatura PK
        int id_usuario FK
        tinyint id_plano FK
        date data_inicio
        date data_fim
        enum status
    }
    PLANO {
        tinyint id_plano PK
        varchar nome_plano UK
        decimal preco_mensal
    }
    CONTEUDO {
        int id_conteudo PK
        varchar titulo
        enum tipo
        year ano_lancamento
    }
    EPISODIO {
        int id_episodio PK
        int id_conteudo FK
        int numero_temporada
        int numero_episodio
    }
    GENERO {
        int id_genero PK
        varchar nome_genero UK
    }
    CONTEUDO_GENERO {
        int id_conteudo PK, FK
        int id_genero PK, FK
    }
    HISTORICO_VISUALIZACAO {
        bigint id_historico PK
        int id_perfil FK
        int id_conteudo FK
        int id_episodio FK
        datetime data_hora_inicio
        int tempo_assistido_min
        boolean concluido
    }
```

## Observações sobre o modelo

- Usuários podem possuir vários perfis e assinaturas ao longo do tempo.
- Conteúdos e gêneros possuem relacionamento muitos-para-muitos, resolvido pela tabela associativa `conteudo_genero`.
- Um conteúdo do tipo série pode possuir episódios; o histórico pode apontar para um episódio específico.
- `id_episodio` é opcional no histórico, permitindo registros de filmes.
- A estrutura representa um cenário didático e usa dados fictícios de demonstração.
