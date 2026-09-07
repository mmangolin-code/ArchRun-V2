from app.schemas import SystemArchitecture

def validate_architecture_semantics(arch: SystemArchitecture) -> list[str]:
    """Identifica anomalias e erros estruturais na arquitetura."""
    issues = []
    
    # 1. Checagem de Pontos Únicos de Falha (SPOFs)
    for node in arch.nodes:
        if node.replicas == 1:
            issues.append(f"Ponto Único de Falha (SPOF): O componente '{node.id}' possui apenas 1 réplica.")
            
    # 2. Checagem de Dependências Síncronas sem Timeout
    for edge in arch.edges:
        if edge.call_type == "sync" and edge.timeout_ms is None:
            issues.append(f"Risco de Cascata: A chamada síncrona de '{edge.source}' para '{edge.target}' não possui timeout configurado.")
            
    # 3. Checagem de Retries sem Backoff em chamadas síncronas
    for edge in arch.edges:
        retries = edge.retries if edge.retries is not None else 0
        if edge.call_type == "sync" and retries > 0:
            issues.append(f"Amplificação de Carga: A chamada '{edge.source}' -> '{edge.target}' possui {retries} retries que podem amplificar falhas.")

    return issues