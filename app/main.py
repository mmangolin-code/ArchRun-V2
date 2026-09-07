from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
from app.llm_parser import parse_architecture_text
from app.engine.validator import validate_architecture_semantics
from app.engine.scenario import simulate_latency_degradation

load_dotenv()

app = FastAPI(
    title="Architecture Reasoning Engine",
    description="Motor de raciocínio determinístico para validação e simulação de arquiteturas.",
    version="1.0.0"
)

class AnalysisRequest(BaseModel):
    architecture_text: str
    question: str


@app.get("/")
def read_root():
    return {"status": "ok", "message": "Architecture Reasoning Engine está rodando."}

@app.post("/parse-only")
def parse_only(text_input: str):
    """Endpoint do Bloco 1: Apenas realiza o parsing e retorna o Modelo Formal JSON."""
    try:
        arch, metrics = parse_architecture_text(text_input)
        return {
            "formal_model": arch.model_dump(),
            "telemetry": metrics
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



@app.post("/analyze")
def analyze(payload: AnalysisRequest):
    try:
        # 1. Parsing extrai o grafo E mapeia a pergunta para um cenário estruturado
        arch, telemetry = parse_architecture_text(payload.architecture_text, payload.question)
        
        # 2. Validação Semântica em Código
        semantic_issues = validate_architecture_semantics(arch)        

        # 2. Se a pergunta for Fora de Escopo, o motor recusa imediatamente (Item 3 do Edital)
        if arch.scenario and arch.scenario.scenario_type == "unsupported":
            return {
                "status": "recusado",
                "motivo": arch.scenario.reason or "A pergunta não é suportada pela matemática analítica deste motor.",
                "telemetry": telemetry
            }

        # 3. Execução da Simulação Dinâmica baseada no nó alvo extraído da pergunta
        target_node = arch.scenario.target_node if arch.scenario else None
        latency_val = arch.scenario.parameter_value if arch.scenario else 3000.0

        simulation_results = simulate_latency_degradation(
            arch, 
            degraded_node_id=target_node or "desconhecido", 
            degraded_latency_ms=latency_val
        )
        
        return {
            "formal_model": arch.model_dump(),
            "semantic_issues": semantic_issues,            
            "simulation_results": simulation_results,
            "telemetry": telemetry
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))