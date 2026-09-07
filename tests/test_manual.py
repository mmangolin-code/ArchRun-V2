import requests

# URL do seu serviço rodando via Docker ou localmente
URL = "http://localhost:8000/reason"

payload = {
    "architecture_text": (
        "A API de checkout chama o serviço de precificação de forma síncrona com timeout de 2s "
        "e 3 tentativas de reexecução (retries). A precificação lê de um único Postgres primário. "
        "O checkout também publica um evento em uma fila consumida pelo worker de faturamento. "
        "O checkout roda 6 réplicas, a precificação 4, cada uma lidando com 80 rps. A meta é 99,9% de disponibilidade."
    ),
    "question": "O que acontece se o Postgres degradar para 3s de tempo de resposta?"
}

response = requests.post(URL, json=payload)

print("Status Code:", response.status_code)
print("Resposta do Motor:\n")
print(response.json())