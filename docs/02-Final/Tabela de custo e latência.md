# Telemetria: Custo e Latência (Modelo Groq / LLaMA-3-70B)

As métricas abaixo foram extraídas a partir dos logs de telemetria da bateria de validação, refletindo o uso de um modelo de processamento ultrarrápido (Groq) otimizado para inferência de JSON.

## Latência P50 e P95
Medição baseada no ciclo completo (Request HTTP -> Parser LLM -> Engenharia Matemática -> Resposta).

| Métrica | Tempo (ms) | Observação |
| :--- | :--- | :--- |
| **p50 (Mediana)** | **1.748 ms** | Reflete cenários bem estruturados e respostas diretas do LLM. |
| **p95 (Cauda)** | **2.619 ms** | Ocorre em descrições mais ambíguas ou arquiteturas maiores, exigindo mais inferência de premissas. |

## Consumo de Tokens (Média por Análise)

| Tipo de Token | Média Consumida |
| :--- | :--- |
| **Tokens de Entrada (Prompt)** | ~1.210 tokens |
| **Tokens de Saída (JSON)** | ~640 tokens |
| **Total por Requisição** | ~1.850 tokens |

## Projeção de Custos para Produção
Assumindo o uso de um modelo hospedado equivalente em performance para extração semântica (ex: precificação de mercado padrão LLaMA 3 70B via APIs em nuvem):
*   **Custo de Entrada (per 1k):** US$ 0,59
*   **Custo de Saída (per 1k):** US$ 0,79

| Análise Individual | Estimativa de Custo |
| :--- | :--- |
| Custo médio por 1 requisição | **~ US$ 0,0012** |
| **Custo Projetado (1.000 análises)** | **~ US$ 1,20** |

*Conclusão:* O custo operacional focado puramente em Parsing tipado (sem RAG ou agentes encadeados) é extremamente marginal. O processador matemático Python roda a custo computacional próximo a zero (O(N) simples), fazendo com que a escala do serviço dependa quase exclusivamente do limite de taxa (Rate Limit) do provedor de LLM escolhido.