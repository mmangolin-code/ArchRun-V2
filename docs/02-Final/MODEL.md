# Modelo Formal e Matemática (MODEL.md)

Este documento descreve o esquema de dados e as fórmulas matemáticas utilizadas pelo motor. Qualquer pessoa pode verificar os cálculos manualmente utilizando estas definições.

## 1. O Modelo Formal (Esquema)
O LLM extrai o texto livre para a seguinte estrutura tipada:

*   **SystemArchitecture**: `nodes` (lista), `edges` (lista), `scenario`, `target_availability`.
*   **Node**: `id` (string), `replicas` (int, default 1), `max_rps_per_replica` (float, nullable).
*   **Edge**: `source` (id), `target` (id), `call_type` (sync/async), `retries` (int), `timeout_ms` (float).
*   **Scenario**: `scenario_type` (degradation, unavailability, load_multiplier), `target_node`, `parameter_value`.


## 2. Fórmulas Matemáticas (Mapeamento com o Código-Fonte)

O motor de cálculos em Python, contido em app/engine/calculator.py e app/engine/scenario.py, utiliza as seguintes fórmulas fechadas:

### A. Carga de Entrada Base (Steady State)

Função: _estimate_base_rps(arch: SystemArchitecture) em scenario.py

Fórmula: Carga_Base = (replicas_entrada * max_rps_entrada) * 0.5

Nota: Assumimos operação normal com 50% de uso do componente que serve de porta de entrada do sistema.
Para simulações de carga, assumimos que o sistema opera normalmente a 50% da capacidade do seu nó de entrada primário.

### B. Saturação / Utilização do Componente
Mede o quanto um nó está estrangulado pela carga.

Função: calculate_node_saturation(effective_rps, replicas, max_rps_per_replica) em calculator.py

Fórmula: Saturacao = effective_rps / (replicas * max_rps_per_replica)

Comportamento: A saída é um índice (ex: 0.8). No scenario.py, isso é formatado para porcentagem (x100). Se a Saturação for >= 1.0, o nó é saturado e quebra a disponibilidade alvo.

*Gatilho de Indisponibilidade:* Se `Saturacao >= 100%`, o nó é considerado indisponível, quebrando a meta de disponibilidade do fluxo.

### C. Carga Efetiva (Amplificação por Retries)
Quando uma chamada **síncrona** falha (por timeout ou indisponibilidade do alvo), os *retries* multiplicam a carga na rede.

Função: calculate_effective_rps(base_rps, retries, target_failing) em calculator.py

Fórmula: Carga_Efetiva = base_rps * (1 + safe_retries)

Comportamento: Quando há um cenário de degradação severa ou indisponibilidade, os retries amplificam diretamente a carga sobre a rede e o alvo.

### D. Latência Acumulada em Cascata
A latência total de um fluxo é a soma do processamento do nó base com a latência de suas chamadas síncronas.

Função: calculate_cascade_latency(node_id, edges, latencies_ms) em calculator.py

Fórmula: Recursiva. Latência_Nó = Base_Ms(Nó) + Sum(Latência_em_Cascata(Chamadas_Sincronas_de_Saida))

*Gatilho de Timeout:* Se `Latencia_Acumulada > timeout_ms` configurado na aresta, a chamada falha, acionando o cálculo de amplificação de carga (D).


## 3. Dinâmica de Cálculo por Cenário

A engine determinística roteia o modelo extraído para fluxos matemáticos específicos dependendo do tipo de cenário identificado:

### Cenário 1: Degradação de Latência (degradation)

Cálculo Acionado: Inicia-se pela Cascata de Latência Síncrona (E). O motor injeta a latência degradada no nó alvo e recalcula a profundidade do grafo.

Gatilho Condicional: Se a nova latência acumulada for maior que o timeout_ms configurado na aresta (conexão), a chamada falha.   

Consequência: A falha dispara o cálculo de Amplificação de Carga (D), multiplicando o tráfego pelas tentativas de retry e espalhando o impacto pelo raio de explosão (Blast Radius). A saturação dos nós afetados também é recalculada.   

### Cenário 2: Indisponibilidade Total (unavailability)

Cálculo Acionado: A latência não é calculada, pois assume-se falha imediata (ex: Connection Refused). O motor busca todas as conexões síncronas que apontam para o nó inativo.   

Consequência Matemática: Para cada conexão síncrona afetada, o motor aplica diretamente a fórmula de Amplificação de Carga (D). Ele calcula o tráfego "inútil" gerado na rede: Carga_Efetiva = Carga_Base * (1 + retries).   

Impacto de Disponibilidade: A disponibilidade dos nós que dependem de forma síncrona do componente inativo cai imediatamente a zero. Conexões assíncronas (filas) não geram amplificação de rede, apenas retenção de mensagens.   

### Cenário 3: Multiplicador de Carga (load_multiplier)

Cálculo Acionado: O motor ignora a latência e foca estritamente no vazão (Throughput). Primeiro, calcula a nova carga de entrada: Carga_Pico = Carga_Base * Multiplicador.   

Consequência Matemática: O motor percorre todos os nós da arquitetura e submete a Carga_Pico à fórmula de Saturação (C).   

Gatilho Condicional: Se o cálculo de saturação de qualquer componente na cadeia resultar em um valor >= 1.0 (100%), aquele componente específico se torna o gargalo (bottleneck). O sistema acusa a quebra da meta de disponibilidade e o nó entra para o raio de impacto.   