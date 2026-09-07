from app.schemas import SystemArchitecture
from app.engine.calculator import calculate_effective_rps, calculate_node_saturation, calculate_cascade_latency

def simulate_latency_degradation(
    arch: SystemArchitecture, 
    degraded_node_id: str, 
    degraded_latency_ms: float,
    input_rps: float = 320.0 # Carga global de entrada do sistema
) -> dict:
    """
    Simula o cenário exigido no enunciado:
    O que acontece se um componente (ex: Postgres) degradar para X ms de tempo de resposta?
    """
    results = {
        "scenario": f"Degradação de latência no componente '{degraded_node_id}' para {degraded_latency_ms}ms",
        "timeouts_exceeded": [],
        "load_amplifications": [],
        "node_saturations": {},
        "blast_radius_impacted_nodes": set(),
        "availability_impact": "Dentro da meta"
    }

    # 1. Mapa de latências base dos nós
    base_latencies = {node.id: 50.0 for node in arch.nodes} # Latência base padronizada
    base_latencies[degraded_node_id] = degraded_latency_ms

    # 2. Avaliar estouro de timeouts e amplificação de carga
    for edge in arch.edges:
        if edge.call_type == "sync":
            # Latência acumulada a partir do alvo
            target_latency = calculate_cascade_latency(edge.target, arch.edges, base_latencies)
            
            # Checa se excede o timeout do cliente
            if edge.timeout_ms and target_latency > edge.timeout_ms:
                results["timeouts_exceeded"].append(
                    f"A chamada '{edge.source}' -> '{edge.target}' excede o timeout de {edge.timeout_ms}ms (Latência real: {target_latency}ms)"
                )
                
                # Aplica amplificação de carga devido a retries
                effective_rps = calculate_effective_rps(input_rps, edge.retries, target_failing=True)
                amplification_factor = 1 + edge.retries
                
                results["load_amplifications"].append(
                    f"As reexecuções do {edge.source} amplificam a carga no {edge.target} em {amplification_factor}x (Carga efetiva: {effective_rps} rps)"
                )
                
                # Marca nós afetados no Blast Radius
                results["blast_radius_impacted_nodes"].add(edge.source)
                results["blast_radius_impacted_nodes"].add(edge.target)

    # 3. Avaliar saturação dos nós sob carga amplificada
    for node in arch.nodes:
        # Se for nó de destino amplificado, avalia a saturação
        max_rps = node.max_rps_per_replica or 80.0
        saturation = calculate_node_saturation(input_rps, node.replicas, max_rps)
        results["node_saturations"][node.id] = f"{saturation * 100}%"
        
        if saturation >= 1.0:
            results["availability_impact"] = f"A disponibilidade cai abaixo da meta ({arch.target_availability * 100}%) devido à saturação de {node.id}"

    # Converter set do Blast Radius para lista contável
    impacted_list = sorted(results["blast_radius_impacted_nodes"])
    results["blast_radius_impacted_nodes"] = impacted_list
    results["blast_radius_summary"] = f"{len(impacted_list)} de {len(arch.nodes)} componentes impactados ({', '.join(impacted_list)})"

    return results