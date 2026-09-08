# Especificação do Modelo Formal e Motor de Cálculo

## 1. Esquema JSON do Modelo Formal
O modelo formal é representado pelo seguinte schema Pydantic:
- `nodes`: Lista de serviços, bancos de dados ou filas (`id`, `replicas`, `max_rps_per_replica`, `timeout_ms`).
- `edges`: Relações de chamada (`source`, `target`, `call_type` ['sync'/'async'], `retries`, `backoff`, `timeout_ms`).

## 2. Formulação Matemática (Código Determinístico)

### A. Amplificação de Carga por Reexecuções (Retries)
Se o serviço alvo falhar ou exceder o timeout em chamadas síncronas:
$$RPS_{efetivo} = RPS_{entrada} \times (1 + Retries)$$

### B. Taxa de Saturação do Componente
$$Saturação = \frac{RPS_{efetivo}}{Réplicas \times MaxRPS_{por\_réplica}}$$
Se $Saturação \ge 1.0$, o serviço entra em colapso/saturação.

### C. Propagação de Latência em Cadeias Síncronas
$$Latência_{total} = Latência_{própria} + \sum_{dep \in DepsSíncronas} Latência_{dep}$$
Se $Latência_{total} > Timeout_{cliente}$, ocorre erro de Timeout no cliente.

### D. Raio de Impacto (Blast Radius)
Contagem de nós impactados diretamente ou indiretamente pela falha transitiva via dependências síncronas.