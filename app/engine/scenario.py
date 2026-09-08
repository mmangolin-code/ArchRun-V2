from app.schemas import SystemArchitecture
from app.engine.calculator import calculate_effective_rps, calculate_node_saturation, calculate_cascade_latency

def _estimate_base_rps(arch: SystemArchitecture) -> float:
    """
    Calcula uma carga de entrada base defensável (estado estacionário / steady state).
    Assume que o sistema opera a 50% da capacidade do nó de entrada primário em situações normais.
    """
    if not arch.nodes:
        return 100.0 # Fallback seguro
    
    # Usa o primeiro componente descrito como porta de entrada (ex: gateway ou api primária)
    entry_node = arch.nodes[0]
    max_rps = entry_node.max_rps_per_replica or 80.0
    replicas = entry_node.replicas or 1
    
    base_capacity = replicas * max_rps
    return base_capacity * 0.5 # Steady state = 50% da capacidade


def simulate_latency_degradation(
    arch: SystemArchitecture, 
    degraded_node_id: str, 
    degraded_latency_ms: float
) -> dict:
    
    input_rps = _estimate_base_rps(arch) # <-- Removido o hardcode de 320.0
    
    results = {
        "scenario": f"Degradação de latência no componente '{degraded_node_id}' para {degraded_latency_ms}ms",
        "timeouts_exceeded": [],
        "load_amplifications": [],
        "node_saturations": {},
        "blast_radius_impacted_nodes": set(),
        "availability_impact": "Dentro da meta"
    }

    base_latencies = {node.id: 50.0 for node in arch.nodes}
    base_latencies[degraded_node_id] = degraded_latency_ms

    for edge in arch.edges:
        if edge.call_type == "sync":
            target_latency = calculate_cascade_latency(edge.target, arch.edges, base_latencies)
            
            if edge.timeout_ms and target_latency > edge.timeout_ms:
                results["timeouts_exceeded"].append(
                    f"A chamada '{edge.source}' -> '{edge.target}' excede o timeout de {edge.timeout_ms}ms (Latência real: {target_latency}ms)"
                )
                
                retries = edge.retries if edge.retries is not None else 0
                effective_rps = calculate_effective_rps(input_rps, retries, target_failing=True)
                amplification_factor = 1 + retries
                
                results["load_amplifications"].append(
                    f"As reexecuções do {edge.source} amplificam a carga no {edge.target} em {amplification_factor}x (Carga efetiva: {effective_rps} rps)"
                )
                
                results["blast_radius_impacted_nodes"].add(edge.source)
                results["blast_radius_impacted_nodes"].add(edge.target)

    for node in arch.nodes:
        max_rps = node.max_rps_per_replica or 80.0
        # Avalia a saturação usando o input_rps dinâmico
        saturation = calculate_node_saturation(input_rps, node.replicas, max_rps)
        results["node_saturations"][node.id] = f"{saturation * 100}%"
        
        if saturation >= 1.0:
            results["availability_impact"] = f"A disponibilidade cai abaixo da meta ({arch.target_availability * 100}%) devido à saturação de {node.id}"

    impacted_list = sorted(results["blast_radius_impacted_nodes"])
    results["blast_radius_impacted_nodes"] = impacted_list
    results["blast_radius_summary"] = f"{len(impacted_list)} de {len(arch.nodes)} componentes impactados ({', '.join(impacted_list)})"

    return results


def simulate_unavailability(
    arch: SystemArchitecture, 
    unavailable_node_id: str
) -> dict:
    
    input_rps = _estimate_base_rps(arch) # <-- Removido o hardcode
    
    results = {
        "scenario": f"Falha total e indisponibilidade do componente '{unavailable_node_id}'",
        "timeouts_exceeded": [],
        "load_amplifications": [],
        "node_saturations": {},
        "blast_radius_impacted_nodes": {unavailable_node_id},
        "availability_impact": f"A disponibilidade do fluxo que depende de '{unavailable_node_id}' cai a zero."
    }

    for edge in arch.edges:
        if edge.target == unavailable_node_id:
            if edge.call_type == "sync":
                results["timeouts_exceeded"].append(
                    f"A chamada '{edge.source}' -> '{edge.target}' falha imediatamente (Conexão Recusada / Timeout Imediato)."
                )
                
                safe_retries = edge.retries if edge.retries is not None else 0
                effective_rps = calculate_effective_rps(input_rps, safe_retries, target_failing=True)
                amplification_factor = 1 + safe_retries
                
                if safe_retries > 0:
                    results["load_amplifications"].append(
                        f"Sem resposta, os retries do '{edge.source}' amplificam a carga na rede em {amplification_factor}x ({effective_rps} rps inúteis)."
                    )
                
                results["blast_radius_impacted_nodes"].add(edge.source)
            
            elif edge.call_type == "async":
                results["timeouts_exceeded"].append(
                    f"O worker/consumidor '{edge.target}' está inativo. Mensagens originadas em '{edge.source}' ficarão retidas na fila/tópico."
                )

    impacted_list = sorted(list(results["blast_radius_impacted_nodes"]))
    results["blast_radius_impacted_nodes"] = impacted_list
    results["blast_radius_summary"] = f"{len(impacted_list)} de {len(arch.nodes)} componentes impactados no sistema ({', '.join(impacted_list)})"

    return results    


def simulate_load_multiplier(
    arch: SystemArchitecture,
    multiplier: float
) -> dict:
    """
    Simula o cenário exigido: O que acontece se a carga multiplicar por N?
    """
    input_rps = _estimate_base_rps(arch)
    peak_load = input_rps * multiplier
    
    results = {
        "scenario": f"Carga de entrada multiplicada em {multiplier}x (Pico estimado: {peak_load} rps)",
        "node_saturations": {},
        "availability_impact": "Dentro da meta",
        "blast_radius_impacted_nodes": set(),
        "timeouts_exceeded": [],
        "load_amplifications": [f"Tráfego externo aumentou de {input_rps} rps para {peak_load} rps"]
    }
    
    for node in arch.nodes:
        max_rps = node.max_rps_per_replica or 80.0
        saturation = calculate_node_saturation(peak_load, node.replicas, max_rps)
        
        results["node_saturations"][node.id] = f"{saturation * 100}%"
        
        # Se a saturação passar de 1.0 (100%), o sistema cai
        if saturation >= 1.0:
            results["availability_impact"] = f"A disponibilidade cai abaixo da meta ({arch.target_availability * 100}%). Gargalo atingido em '{node.id}'."
            results["blast_radius_impacted_nodes"].add(node.id)
            
    impacted_list = sorted(list(results["blast_radius_impacted_nodes"]))
    results["blast_radius_impacted_nodes"] = impacted_list
    results["blast_radius_summary"] = f"{len(impacted_list)} de {len(arch.nodes)} componentes saturaram com o pico."

    return results