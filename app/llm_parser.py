import os
import json
from groq import Groq
from app.schemas import SystemArchitecture
from app.telemetry import TelemetryTracker
from app.prompts import SYSTEM_PROMPT_PARSER


def _normalize_parser_output(parsed_dict: dict) -> dict:
    """Completa apenas a estrutura do contrato; não inventa dados da arquitetura."""
    if not isinstance(parsed_dict, dict):
        raise ValueError("A Groq retornou um JSON que não é um objeto na raiz.")

    normalized = dict(parsed_dict)
    normalized.setdefault("system_name", "Sistema Desconhecido")
    normalized.setdefault("status", "incomplete")
    normalized.setdefault("scenario", None)
    normalized.setdefault("nodes", [])
    normalized.setdefault("edges", [])
    normalized.setdefault("target_availability", 0.999)
    normalized.setdefault("assumptions_made", [])
    normalized.setdefault("missing_critical_info", [])
    normalized.setdefault("reason", None)

    if not isinstance(normalized["missing_critical_info"], list):
        normalized["missing_critical_info"] = []

    nodes = normalized["nodes"] if isinstance(normalized["nodes"], list) else []
    valid_nodes = []
    for node in nodes:
        if isinstance(node, dict) and node.get("id"):
            valid_nodes.append(node)
        else:
            normalized["missing_critical_info"].append(
                "Um componente foi descartado porque não possuía um id válido."
            )
    normalized["nodes"] = valid_nodes

    edges = normalized["edges"] if isinstance(normalized["edges"], list) else []
    valid_edges = []
    for edge in edges:
        if (
            isinstance(edge, dict)
            and edge.get("source")
            and edge.get("target")
            and edge.get("call_type") in {"sync", "async"}
        ):
            valid_edges.append(edge)
        else:
            normalized["missing_critical_info"].append(
                "Uma conexão foi descartada porque não possuía source, target ou call_type válidos."
            )
    normalized["edges"] = valid_edges

    scenario = normalized["scenario"]
    if isinstance(scenario, str):
        normalized["scenario"] = {
            "scenario_type": scenario,
            "target_node": None,
            "parameter_value": None,
            "reason": None,
        }
    elif isinstance(scenario, dict):
        scenario = dict(scenario)
        scenario_type = scenario.get("scenario_type")
        if scenario_type not in {
            "degradation",
            "unavailability",
            "load_multiplier",
            "unsupported",
        }:
            normalized["scenario"] = None
            normalized["missing_critical_info"].append(
                "O cenário foi descartado porque scenario_type não era válido."
            )
        else:
            scenario.setdefault("target_node", None)
            scenario.setdefault("parameter_value", None)
            scenario.setdefault("reason", None)
            normalized["scenario"] = scenario

    if not isinstance(normalized["target_availability"], (int, float)):
        normalized["target_availability"] = 0.999

    return normalized

def parse_architecture_text(text: str, question: str | None = None) -> tuple[SystemArchitecture, dict]:
    tracker = TelemetryTracker()
    tracker.start()
    
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError("A variável de ambiente GROQ_API_KEY não foi configurada no arquivo .env")

    client = Groq(api_key=api_key)
    
    user_content = f"Descrição da arquitetura:\n{text}"
    if question:
        user_content += f"\n\nPergunta a ser analisada:\n{question}"

    completion = client.chat.completions.create(
            model=os.environ.get("MODEL_NAME", "openai/gpt-oss-120b"),
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT_PARSER},
                {"role": "user", "content": user_content}
            ],
            response_format={"type": "json_object"},
            temperature=0.0
    )
    
    tokens_in = getattr(completion.usage, 'prompt_tokens', 0)
    tokens_out = getattr(completion.usage, 'completion_tokens', 0)
    metrics = tracker.stop(tokens_in=tokens_in, tokens_out=tokens_out)
    
    raw_json = completion.choices[0].message.content
    if not raw_json:
        raise ValueError("A Groq retornou uma resposta vazia para o parser.")

    try:
        parsed_dict = _normalize_parser_output(json.loads(raw_json))
    except json.JSONDecodeError as error:
        preview = raw_json[:500].replace("\n", " ")
        raise ValueError(
            f"A Groq retornou JSON inválido na posição {error.pos}: {preview}"
        ) from error
    
    return SystemArchitecture(**parsed_dict), metrics

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    
    # Texto completo do enunciado do desafio
    sample_text = (
        "A API de checkout chama o serviço de precificação de forma síncrona com timeout de 2s "
        "e 3 tentativas de reexecução (retries). A precificação lê de um único Postgres primário. "
        "O checkout também publica um evento em uma fila consumida pelo worker de faturamento. "
        "O checkout roda 6 réplicas, a precificação 4, cada uma lidando com 80 rps. A meta é 99,9% de disponibilidade."
    )
    print("--- Testando Parser Isoladamente (Texto Completo) ---")
    try:
        arch, tele = parse_architecture_text(sample_text)
        print("Modelo Formal Extraído com Sucesso:")
        print(arch.model_dump_json(indent=2))
        print("\nMétricas de Telemetria:", tele)
    except Exception as e:
        print("Erro ao executar parser:", e)