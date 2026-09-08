# Modelo Formal e Matemática (MODEL.md)

Este documento descreve o esquema de dados e as fórmulas matemáticas utilizadas pelo motor. Qualquer pessoa pode verificar os cálculos manualmente utilizando estas definições.

## 1. O Modelo Formal (Esquema)
O LLM extrai o texto livre para a seguinte estrutura tipada:

*   **SystemArchitecture**: `nodes` (lista), `edges` (lista), `scenario`, `target_availability`.
*   **Node**: `id` (string), `replicas` (int, default 1), `max_rps_per_replica` (float, nullable).
*   **Edge**: `source` (id), `target` (id), `call_type` (sync/async), `retries` (int), `timeout_ms` (float).
*   **Scenario**: `scenario_type` (degradation, unavailability, load_multiplier), `target_node`, `parameter_value`.

## 2. Fórmulas Matemáticas

A engine utiliza cálculos analíticos de forma fechada.

### A. Capacidade Total de um Nó
A capacidade de um componente é o produto de suas réplicas pela sua capacidade individual.
```text
Capacidade_Total = replicas * max_rps_per_replica
```
*(Nota: Se max_rps_per_replica for nulo, a capacidade é considerada infinita / irrestrita, resultando em saturação 0%).*

### B. Carga de Entrada Estimada (Steady State)
Para simulações de carga, assumimos que o sistema opera normalmente a 50% da capacidade do seu nó de entrada primário.
```text
Carga_Base = Capacidade_Total(Nó_Entrada) * 0.5
Carga_Pico = Carga_Base * Multiplicador_de_Carga
```

### C. Saturação (Utilização)
Mede o quanto um nó está estrangulado pela carga.
```text
Saturacao = (Carga_Efetiva_Recebida / Capacidade_Total) * 100
```
*Gatilho de Indisponibilidade:* Se `Saturacao >= 100%`, o nó é considerado indisponível, quebrando a meta de disponibilidade do fluxo.

### D. Amplificação de Carga (Retries Storm)
Quando uma chamada **síncrona** falha (por timeout ou indisponibilidade do alvo), os *retries* multiplicam a carga na rede.
```text
Carga_Amplificada = Carga_Base * (1 + retries)
```

### E. Cascata de Latência Síncrona
A latência total de um fluxo é a soma do processamento do nó base com a latência de suas chamadas síncronas.
```text
Latencia_Acumulada(A) = Latencia_Base(A) + Sum( Latencia_Acumulada(Destinos_Sincronos) )
```
*Gatilho de Timeout:* Se `Latencia_Acumulada > timeout_ms` configurado na aresta, a chamada falha, acionando o cálculo de amplificação de carga (D).