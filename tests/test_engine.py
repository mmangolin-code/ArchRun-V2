from app.schemas import SystemArchitecture, Node, Edge
from app.engine.scenario import simulate_latency_degradation

# 1. Monta o Grafo Formal exatamente como o Bloco 1 extrai
arch = SystemArchitecture(
    nodes=[
        Node(id="checkout", replicas=6, max_rps_per_replica=80.0, timeout_ms=2000.0),
        Node(id="pricing", replicas=4, max_rps_per_replica=80.0, timeout_ms=2000.0),
        Node(id="postgres-primary", replicas=1, max_rps_per_replica=500.0, timeout_ms=None),
        Node(id="faturamento-worker", replicas=1, max_rps_per_replica=None, timeout_ms=None)
    ],
    edges=[
        Edge(source="checkout", target="pricing", call_type="sync", retries=3, timeout_ms=2000.0),
        Edge(source="pricing", target="postgres-primary", call_type="sync", retries=0, timeout_ms=None),
        Edge(source="checkout", target="faturamento-worker", call_type="async", retries=0, timeout_ms=None)
    ],
    target_availability=0.999
)

# 2. Executa a simulação: "O que acontece se o Postgres degradar para 3000ms?"
output = simulate_latency_degradation(arch, degraded_node_id="postgres-primary", degraded_latency_ms=3000.0)

print("--- RESULTADO DA MATEMÁTICA PURA (SEM LLM) ---")
import json
print(json.dumps(output, indent=2, ensure_ascii=False))
