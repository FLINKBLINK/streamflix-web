# Catálogo de métricas

## Consumo

| Métrica | Regra | Observação |
|---|---|---|
| Visualizações | Quantidade de registros em `historico_visualizacao` | Contagem de registros, não de pessoas únicas. |
| Horas assistidas | Soma de `tempo_assistido_min` dividida por 60 | Depende da qualidade dos registros. |
| Taxa de conclusão | Registros com `concluido = 1` / total de registros × 100 | Usa o campo booleano de conclusão. |
| Conteúdos assistidos | Quantidade de conteúdos distintos com histórico no período | Cada conteúdo conta uma vez nesse indicador. |
| Média assistida | Soma de minutos assistidos / quantidade de reproduções | Calculada por conteúdo. |
| Reproduções concluídas | Quantidade de registros com `concluido = 1` | Não equivale a usuários únicos. |

## Receita mensal estimada

A aplicação soma `plano.preco_mensal` das assinaturas cujo status é `ATIVA`. É uma estimativa contratual simples; não considera descontos, inadimplência, prorrateio, impostos, reembolsos ou confirmação de pagamento. Não deve ser interpretada como receita contábil.

## Filtros e validação

Os endpoints de analytics compartilham a validação de tipo, gênero e período. O tipo permitido é `FILME` ou `SERIE`; as datas devem estar no formato ISO `AAAA-MM-DD`, e a data inicial não pode ser posterior à final. A data final é inclusiva: os registros são filtrados até o início do dia seguinte. Datas inválidas retornam HTTP 400 em vez de serem enviadas diretamente às consultas SQL.

Conteúdos sem visualizações no período continuam no ranking com valores zerados.

## Limitações

A base é pequena e fictícia, voltada à demonstração acadêmica. As métricas descrevem os registros disponíveis, não comportamento real de mercado.
