import os
import json
from groq import Groq
from app.schemas import SystemArchitecture
from app.telemetry import TelemetryTracker
from app.prompts import SYSTEM_PROMPT_PARSER

def parse_architecture_text(text: str) -> tuple[SystemArchitecture, dict]:
    tracker = TelemetryTracker()
    tracker.start()
    
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError("A variável de ambiente GROQ_API_KEY não foi configurada no arquivo .env")

    client = Groq(api_key=api_key)
    
    completion = client.chat.completions.create(
            model=os.environ.get("MODEL_NAME", "openai/gpt-oss-120b"),
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT_PARSER},
                {"role": "user", "content": f"Descrição da arquitetura:\n{text}"}
            ],
            response_format={"type": "json_object"},
            temperature=0.0
    )
    
    tokens_in = getattr(completion.usage, 'prompt_tokens', 0)
    tokens_out = getattr(completion.usage, 'completion_tokens', 0)
    metrics = tracker.stop(tokens_in=tokens_in, tokens_out=tokens_out)
    
    raw_json = completion.choices[0].message.content
    parsed_dict = json.loads(raw_json)
    
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