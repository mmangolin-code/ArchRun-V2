# NENHUM MODELO DE LINGUAGEM AQUI. APENAS CÓDIGO PYTHON TESTÁVEL.
"""
def calculate_effective_rps(base_rps: float, retries: int, is_failed: bool) -> float:
    Calcula o RPS efetivo com base em falhas e reexecuções síncronas.
    if is_failed:
        return base_rps * (1 + retries)
    return base_rps

def calculate_saturation(node_effective_rps: float, replicas: int, max_rps_per_replica: float) -> float:
    Calcula a taxa de utilização/saturação do componente.
    capacity = replicas * max_rps_per_replica
    return node_effective_rps / capacity if capacity > 0 else float('inf')
"""


"""
import math

def calculate_effective_rps(base_rps: float, retries: int, target_failing: bool) -> float:
    #Calcula a carga amplificada em caso de falha/timeout na dependência.
    if target_failing:
        # Cada tentativa falha resulta em (1 + retries) chamadas totais
        return base_rps * (1 + retries)
    return base_rps

def calculate_node_saturation(effective_rps: float, replicas: int, max_rps_per_replica: float | None) -> float:
    #Calcula a taxa de utilização/saturação do nó (1.0 = 100% saturado).
    if max_rps_per_replica is None or max_rps_per_replica <= 0:
        return 0.0 # Sem limite declarado ou irrestrito no modelo
    
    capacity = replicas * max_rps_per_replica
    return round(effective_rps / capacity, 2)

def calculate_cascade_latency(node_id: str, edges: list, latencies_ms: dict) -> float:
    #Calcula a latência acumulada síncrona a partir de um nó inicial.
    total_latency = latencies_ms.get(node_id, 0.0)
    
    for edge in edges:
        if edge.source == node_id and edge.call_type == "sync":
            total_latency += calculate_cascade_latency(edge.target, edges, latencies_ms)
            
    return total_latency
"""

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
    safe_max_rps = max_rps_per_replica if max_rps_per_replica is not None else 80.0
    
    if safe_max_rps <= 0:
        return 0.0 
    
    capacity = safe_replicas * safe_max_rps
    return round(effective_rps / capacity, 2)

def calculate_cascade_latency(node_id: str, edges: list, latencies_ms: dict) -> float:
    total_latency = latencies_ms.get(node_id, 0.0)
    for edge in edges:
        if edge.source == node_id and edge.call_type == "sync":
            total_latency += calculate_cascade_latency(edge.target, edges, latencies_ms)
    return total_latency