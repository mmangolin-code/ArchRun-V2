"""
from pydantic import BaseModel, Field
from typing import List, Literal, Optional

class Node(BaseModel):
    id: str
    replicas: int = 1
    max_rps_per_replica: Optional[float] = None
    timeout_ms: Optional[float] = None

class Edge(BaseModel):
    source: str
    target: str
    call_type: Literal["sync", "async"]
    retries: int = 0
    timeout_ms: Optional[float] = None

class SystemArchitecture(BaseModel):
    nodes: List[Node]
    edges: List[Edge]
    target_availability: Optional[float] = 0.999
"""    

    
from pydantic import BaseModel, Field
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
    timeout_ms: Optional[float] = None

class SimulationScenario(BaseModel):
    scenario_type: Literal["degradation", "unavailability", "load_multiplier", "unsupported"]
    target_node: Optional[str] = None
    parameter_value: Optional[float] = None
    reason: Optional[str] = None

class SystemArchitecture(BaseModel):
    nodes: List[Node]
    edges: List[Edge]
    target_availability: float = 0.999
    scenario: Optional[SimulationScenario] = None    