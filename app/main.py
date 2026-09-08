import logging

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
from app.llm_parser import parse_architecture_text
from app.engine.validator import validate_architecture_semantics
from app.engine.scenario import simulate_latency_degradation, simulate_unavailability, simulate_load_multiplier

logger = logging.getLogger(__name__)

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
        logger.exception("Falha no endpoint /parse-only")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/analyze")
def analyze(payload: AnalysisRequest):
    try:
        # 1. Parsing extrai o grafo e mapeia a pergunta
        arch, telemetry = parse_architecture_text(payload.architecture_text, payload.question)
        
        # 2. Verifica se a descrição é INSUFICIENTE (Bloqueante)
        if arch.status == "incomplete":
            return {
                "status": "recusado_por_falta_de_dados",
                "mensagem": "A descrição da arquitetura não possui detalhes suficientes para uma simulação matemática precisa. Por favor, complemente sua solicitação.",
                "informacoes_faltantes": arch.missing_critical_info,
                "telemetry": telemetry
            }

        # 3. Verifica se a pergunta é FORA DE ESCOPO ou NULA (Bloqueante)
        if not arch.scenario or arch.scenario.scenario_type == "unsupported":
            return {
                "status": "recusado_fora_de_escopo",
                "motivo": arch.scenario.reason if arch.scenario else "Não foi possível identificar um cenário de simulação suportado na pergunta.",
                "telemetry": telemetry
            }

        scenario_type = arch.scenario.scenario_type

        # 4. Roteamento e Simulação Matemática
 # 4. Roteamento e Simulação Matemática
        if scenario_type == "degradation":
            target_node = arch.scenario.target_node or "desconhecido"
            latency_val = arch.scenario.parameter_value or 3000.0
            
            simulation_results = simulate_latency_degradation(
                arch, 
                degraded_node_id=target_node, 
                degraded_latency_ms=latency_val
            )
            
        elif scenario_type == "unavailability":
            target_node = arch.scenario.target_node or "desconhecido"
            
            simulation_results = simulate_unavailability(
                arch,
                unavailable_node_id=target_node
            )

        elif scenario_type == "load_multiplier":
            # Extrai o fator de multiplicação mapeado pelo parser (ex: tráfego 5x)
            multiplier_val = arch.scenario.parameter_value or 2.0
            
            simulation_results = simulate_load_multiplier(
                arch,
                multiplier=multiplier_val
            )
            
        # 5. Retorno Final (Sucesso + Alertas da Casca Determinística)
        return {
            "status": "sucesso_com_alertas" if arch.semantic_issues else "sucesso",
            "formal_model": arch.model_dump(exclude={"semantic_issues"}), 
            "semantic_issues": arch.semantic_issues, 
            "simulation_results": simulation_results,
            "telemetry": telemetry
        }
    
    except Exception as e:
        logger.exception("Falha no endpoint /analyze")
        raise HTTPException(status_code=500, detail=str(e))