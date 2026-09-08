# Conjunto de Validação e Análise de Erros (VALIDATION.md)

Este documento reporta a execução do conjunto de validação, os resultados obtidos e a análise crítica das falhas encontradas.

## 1. Cobertura da Validação
Foram executados **12 cenários de teste** cobrindo:
*   Degradação de latência com e sem retries (Amplificação e Risco de Cascata).
*   Indisponibilidade de componentes síncronos (SPOFs) e assíncronos (Isolamento de falhas).
*   Multiplicação de carga (Saturação de gargalos).
*   Entradas adversariais: Textos incompletos, fora de escopo e com descrições contraditórias.

A precisão do cálculo matemático (Golden Tests) nos cenários bem estruturados foi de **100%**, correspondendo exatamente às derivações manuais.

## 2. Análise de Erros e Casos de Falha (Lições Aprendidas)

Durante a validação inicial cruzada, identificamos dois casos em que o sistema apresentou comportamentos errôneos devido à fronteira entre LLM e Código.

### Erro 1: Falha na Resolução de Contradições Semânticas (Teste 4.3)
*   **O Caso:** O usuário digitou: *"O worker consome a fila do Kafka de forma síncrona com timeout HTTP de 5s."*
*   **A Falha:** O LLM acatou a contradição e gerou uma aresta do tipo `sync` com timeout de 5s para o consumo de um evento do Kafka.
*   **A Causa:** O `SYSTEM_PROMPT_PARSER` estava passivo. Ele extraía o que lia sem aplicar conhecimento de engenharia de software básico para sobrepor absurdos arquiteturais.
*   **A Correção (Evolução):** A orientação do LLM foi atualizada para atuar ativamente na mitigação de ambiguidades, forçando filas para `async` e registrando a correção no vetor `assumptions_made`.

### Erro 2: O Falso Gargalo na Capacidade Nula (Teste 3.2)
*   **O Caso:** Uma dependência de banco de dados tinha "capacidade irrestrita". O cenário multiplicou a carga por 2x.
*   **A Falha:** O resultado matemático reportou o banco com 625% de saturação.
*   **A Causa:** O LLM extraiu corretamente `max_rps_per_replica: null`. No entanto, na camada determinística Python, o cálculo de saturação usava um *fallback* numérico (`max_rps = max_rps_per_replica or 80.0`). O valor nulo foi convertido para 80 RPS, distorcendo o cálculo perante altos volumes.
*   **A Correção:** A função `calculate_node_saturation` foi alterada. Agora, se `max_rps` for menor ou igual a 0, ou explicitamente anulado, a função retorna `0.0` (0% de saturação), refletindo perfeitamente a matemática de uma capacidade irrestrita.