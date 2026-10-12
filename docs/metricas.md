# Catálogo de métricas

## Consumo

| Métrica | Regra | Observação |
|---|---|---|
| Visualizações | Quantidade de registros em `historico_visualizacao` | É uma contagem de registros, não de pessoas únicas. |
| Horas assistidas | Soma de `tempo_assistido_min` dividida por 60 | Depende da qualidade dos registros do histórico. |
| Taxa de conclusão | Registros com `concluido = 1` / total de registros × 100 | Uma reprodução é considerada concluída quando o campo está marcado como verdadeiro. |
| Conteúdos assistidos | Quantidade de conteúdos distintos com histórico no período | Um mesmo conteúdo conta uma vez nesse indicador. |
| Média assistida | Soma de minutos assistidos / quantidade de reproduções | Calculada por conteúdo. |
| Reproduções concluídas | Quantidade de registros com `concluido = 1` | Não equivale a usuários únicos. |

## Receita mensal estimada

A aplicação soma `plano.preco_mensal` das assinaturas cujo status é `ATIVA`. É uma estimativa contratual simples; não considera descontos, inadimplência, prorrateio, impostos, reembolsos nem confirmação de pagamento. Não deve ser interpretada como receita contábil.

## Filtros

Os indicadores de consumo aceitam tipo, gênero e período. A data final é inclusiva: os registros são filtrados até o final do dia informado. Conteúdos sem visualizações no período continuam no ranking com valores zerados.

## Limitações

A base é pequena e fictícia, voltada à demonstração acadêmica. As métricas descrevem os registros disponíveis, não comportamento real de mercado.
