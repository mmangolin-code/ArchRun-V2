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


# Conjunto de Validação e Análise de Erros (VALIDATION.md)

Este documento reporta a execução do conjunto de validação exigido no desafio, os resultados obtidos nos 12 Golden Tests e a análise crítica da resiliência do sistema.

## 1. Suíte de Testes Determinística

Atendendo aos "Hard Requirements", o projeto inclui uma suíte de testes unitários (tests/test_engine.py) escrita com pytest.

Isolamento do Modelo de Linguagem: Os testes instanciam o modelo formal (SystemArchitecture) diretamente via dicionários Python, contornando a chamada ao LLM.

Prova Matemática: Isso garante que os cálculos de saturação, timeouts e amplificação de carga sejam verificados de forma determinística, provando que o código Python funciona como uma calculadora confiável independente da IA.

## 2. Cobertura da Validação (12 Casos de Teste)

O motor foi submetido a 4 cenários principais, deriváveis analiticamente à mão:

### Cenário 1: Degradação de Latência (degradation)

1.1 O Exemplo Canônico: 
Degradação no Postgres estourou o timeout do cliente e ativou a matemática de retry storm, registrando amplificação de 4x na carga. (Aprovado).

1.2 Risco de Cascata Oculto: 
Chamada síncrona sem timeout não gerou estourou erro imediato de rede, mas apontou "Risco de Cascata" na validação semântica. (Aprovado).

1.3 Degradação Segura: 
Degradação de 5s num sistema com 15s de timeout foi contida com sucesso. (Aprovado).

## Cenário 2: 
Indisponibilidade Total (unavailability)

2.1 SPOF Síncrono Fatal: 
Queda de um serviço antifraude único derrubou o gateway devido à dependência síncrona. (Aprovado).

2.2 Isolamento por Assincronia: 
Falha no worker de mensageria (RabbitMQ) não impactou a disponibilidade da API de origem. (Aprovado).

2.3 Efeito Dominó de Retries: 
Múltiplos níveis de serviço com retries aninhados multiplicaram agressivamente a carga na rede. (Aprovado).

## Cenário 3: Multiplicador de Carga (load_multiplier)

3.1 Saturação Massiva: 
Um pico de 5x na Black Friday excedeu os 200 RPS de capacidade máxima, derrubando o sistema. (Aprovado).

3.2 Pico Absorvido (Corrigido): 
Pico de 2x absorvido perfeitamente. O banco de dados com max_rps_per_replica: null marcou 0% de saturação (capacidade irrestrita tratada corretamente). (Aprovado).

3.3 Assimetria de Escala: 
A API escalou até 20 réplicas, mas estrangulou o banco primário fixo. (Aprovado).

## Cenário 4: Validações Adversariais e Casos de Borda

4.1 Descrição Incompleta: 
O LLM identificou falta de dados topológicos críticos, ativou o status incomplete e o motor recusou o cálculo, exibindo o array missing_critical_info. (Aprovado).

4.2 Fora de Escopo: 
Pergunta sobre vazamento de chaves no GitHub foi rechaçada ativamente (cenário unsupported), cumprindo a regra de não calcular números onde não há suporte matemático. (Aprovado).

4.3 Texto Contraditório (Corrigido): 
O input continha um "worker consumindo fila de forma síncrona com timeout HTTP". O parser corrigiu a anomalia arquitetural, forçou o modelo assíncrono e registrou a interferência em assumptions_made. (Aprovado).

## 3. Análise de Erros e Evolução do Modelo

Durante as iterações da construção dos 12 testes, dois ajustes críticos foram necessários:

Resolução de Ambiguidade (Erro no Teste 4.3): 
Inicialmente, o LLM transcrevia a contradição arquitetural do usuário fielmente. Tivemos que alterar o SYSTEM_PROMPT_PARSER para atuar de forma ativa, orientando o LLM a aplicar princípios de engenharia de software para forçar conexões de fila como async, garantindo um modelo formal funcional.

O Bug do Gargalo Falso (Erro no Teste 3.2): 
O código original transformava campos numéricos nulos (None) em um padrão fixo de 80 RPS. Isso fazia bancos de dados "irrestritos" falharem falsamente sob altas cargas. O script calculator.py foi ajustado para entender valores nulos de limite de RPS como capacidade infinita (retornando saturação 0.0), corrigindo a distorção matemática.