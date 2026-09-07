import time

class TelemetryTracker:
    def __init__(self):
        self.start_time = None

    def start(self):
        self.start_time = time.time()

    def stop(self, tokens_in: int = 0, tokens_out: int = 0, cost_per_1k_in: float = 0.00059, cost_per_1k_out: float = 0.00079) -> dict:
        latency_ms = round((time.time() - self.start_time) * 1000, 2) if self.start_time else 0.0
        total_tokens = tokens_in + tokens_out
        
        # Custo aproximado baseado na tabela da API escolhida (ex: Groq / Gemini / OpenAI)
        cost_usd = (tokens_in / 1000.0 * cost_per_1k_in) + (tokens_out / 1000.0 * cost_per_1k_out)
        
        return {
            "latency_ms": latency_ms,
            "tokens_in": tokens_in,
            "tokens_out": tokens_out,
            "total_tokens": total_tokens,
            "estimated_cost_usd": round(cost_usd, 6)
        }
