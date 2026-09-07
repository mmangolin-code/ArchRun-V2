#from pydantic import BaseModel, Field, model_validator
#from typing import List, Literal, Optional

    
from pydantic import BaseModel, Field, model_validator
from typing import List, Literal, Optional

class Node(BaseModel):
    id: str
    replicas: Optional[int] = 1
    max_rps_per_replica: Optional[float] = None
    timeout_ms: Optional[float] = None

class Edge(BaseModel):
    source: str
    target: str
    call_type: Literal["sync", "async"]
    retries: Optional[int] = 0
    backoff_ms: Optional[float] = None # <-- Adicionado
    timeout_ms: Optional[float] = None

class SimulationScenario(BaseModel):
    scenario_type: Literal["degradation", "unavailability", "load_multiplier", "unsupported"]
    target_node: Optional[str] = None
    parameter_value: Optional[float] = None
    reason: Optional[str] = None

class SystemArchitecture(BaseModel):
    system_name: Optional[str] = "Sistema Desconhecido"
    status: Literal["ready", "incomplete", "unsupported"] = "ready"
    nodes: List[Node]
    edges: List[Edge]
    target_availability: float = 0.999
    scenario: Optional[SimulationScenario] = None
    assumptions_made: List[str] = Field(default_factory=list) # <-- Adicionado
    missing_critical_info: List[str] = Field(default_factory=list) # <-- Adicionado
    reason: Optional[str] = None # <-- Adicionado

    # Campo para armazenar os avisos semânticos gerados pela validação
    semantic_issues: List[str] = Field(default_factory=list)

    @model_validator(mode='after')
    def check_semantics(self) -> 'SystemArchitecture':
        issues = []
        
        # 1. Checagem de Pontos Únicos de Falha (SPOFs)
        for node in self.nodes:
            if getattr(node, 'replicas', 1) == 1:
                issues.append(f"Ponto Único de Falha (SPOF): O componente '{node.id}' possui apenas 1 réplica.")
                
        # 2. Checagem de Dependências Síncronas
        for edge in self.edges:
            if getattr(edge, 'call_type', '') == "sync":
                if getattr(edge, 'timeout_ms', None) is None:
                    issues.append(f"Risco de Cascata: A chamada síncrona de '{edge.source}' para '{edge.target}' não possui timeout configurado.")
                
                retries = getattr(edge, 'retries', 0)
                if retries is not None and retries > 0:
                    issues.append(f"Amplificação de Carga: A chamada '{edge.source}' -> '{edge.target}' possui {retries} retries que podem amplificar falhas.")
        
        # Atribui os problemas encontrados ao campo do modelo
        self.semantic_issues = issues
        return self