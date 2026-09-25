# NENHUM MODELO DE LINGUAGEM AQUI. APENAS CÓDIGO PYTHON TESTÁVEL.

import math

def calculate_effective_rps(base_rps: float, retries: int | None, target_failing: bool) -> float:
    """Calcula a carga amplificada com proteção contra valores nulos."""
    safe_retries = retries if retries is not None else 0
    if target_failing:
        return base_rps * (1 + safe_retries)
    return base_rps

def calculate_node_saturation(effective_rps: float, replicas: int | None, max_rps_per_replica: float | None) -> float:
    """Calcula saturação assumindo valores default seguros caso o LLM retorne null."""
    safe_replicas = replicas if replicas is not None else 1

    if max_rps_per_replica is None:
        return 0.0

    safe_max_rps = max_rps_per_replica

    if safe_max_rps <= 0 or safe_replicas <= 0:
        # Se efetivamente está recebendo carga mas não tem capacidade, é saturação infinita
        return float('inf') if effective_rps > 0 else 0.0

    capacity = safe_replicas * safe_max_rps
    return round(effective_rps / capacity, 2)

def calculate_cascade_latency(node_id: str, edges: list, latencies_ms: dict) -> float:
    total_latency = latencies_ms.get(node_id, 0.0)
    for edge in edges:
        if edge.source == node_id and edge.call_type == "sync":
            total_latency += calculate_cascade_latency(edge.target, edges, latencies_ms)
    return total_latency