# Consultas SQL para validação

As consultas abaixo permitem conferir, diretamente no MySQL, os resultados apresentados na tela de desempenho do catálogo.

## Visualizações por conteúdo

```sql
SELECT
    c.id_conteudo,
    c.titulo,
    c.tipo,
    COUNT(h.id_historico) AS visualizacoes,
    ROUND(COALESCE(SUM(h.tempo_assistido_min), 0) / 60, 2) AS horas_assistidas,
    ROUND(COALESCE(AVG(h.tempo_assistido_min), 0), 1) AS media_minutos_assistidos,
    COALESCE(SUM(CASE WHEN h.concluido = 1 THEN 1 ELSE 0 END), 0)
        AS reproducoes_concluidas,
    ROUND(
        COALESCE(
            100 * SUM(CASE WHEN h.concluido = 1 THEN 1.0 ELSE 0.0 END)
            / NULLIF(COUNT(h.id_historico), 0),
            0
        ),
        1
    ) AS taxa_conclusao
FROM conteudo c
LEFT JOIN historico_visualizacao h
    ON h.id_conteudo = c.id_conteudo
GROUP BY c.id_conteudo, c.titulo, c.tipo
ORDER BY visualizacoes DESC, c.titulo;
```

## Conferir a quantidade de registros de histórico

```sql
SELECT COUNT(*) AS total_registros
FROM historico_visualizacao;
```

Para reproduzir os filtros do dashboard, acrescente as condições de tipo, gênero e período correspondentes. Use os dados de demonstração somente para fins acadêmicos.
