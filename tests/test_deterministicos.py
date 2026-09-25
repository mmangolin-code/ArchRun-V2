import pytest
from app.schemas import SystemArchitecture
from app.engine.scenario import (
    simulate_latency_degradation,
    simulate_unavailability,
    simulate_load_multiplier
)

# ==========================================
# CENÁRIO 1: DEGRADAÇÃO DE LATÊNCIA
# ==========================================
def test_degradation_amplification_and_timeout():
    """
    Golden Test 1.1: O Exemplo Canônico.
    Prova que o timeout estoura e a carga é amplificada pelos retries.
    """
    # Modelo Formal Injetado Diretamente (Bypass do LLM)
    arch = SystemArchitecture(**{
        "system_name": "checkout_system",
        "nodes": [
            {"id": "checkout", "replicas": 6, "max_rps_per_replica": 80.0},
            {"id": "pricing", "replicas": 4, "max_rps_per_replica": 80.0},
            {"id": "postgres", "replicas": 1, "max_rps_per_replica": None}
        ],
        "edges": [
            {"source": "checkout", "target": "pricing", "call_type": "sync", "retries": 3, "timeout_ms": 2000.0},
            {"source": "pricing", "target": "postgres", "call_type": "sync"}
        ]
    })

    result = simulate_latency_degradation(arch, degraded_node_id="postgres", degraded_latency_ms=3000.0)

    # Asserções Matemáticas
    assert len(result["timeouts_exceeded"]) == 1
    assert "2000.0ms" in result["timeouts_exceeded"][0]
    
    # Verifica amplificação de carga (1 chamada + 3 retries = 4x)
    assert len(result["load_amplifications"]) == 1
    assert "4x" in result["load_amplifications"][0]
    
    # Verifica o Raio de Impacto
    assert "checkout" in result["blast_radius_impacted_nodes"]
    assert "pricing" in result["blast_radius_impacted_nodes"]

# ==========================================
# CENÁRIO 2: INDISPONIBILIDADE TOTAL
# ==========================================
def test_unavailability_async_isolation():
    """
    Golden Test 2.2: Isolamento por Assincronia.
    Prova que falhas em dependências assíncronas não estouram timeouts nem amplificam carga síncrona.
    """
    arch = SystemArchitecture(**{
        "system_name": "Order System",
        "nodes": [
            {"id": "api-pedidos", "replicas": 1, "max_rps_per_replica": None},
            {"id": "rabbitmq", "replicas": 1, "max_rps_per_replica": None},
            {"id": "worker-notificacao", "replicas": 1, "max_rps_per_replica": None}
        ],
        "edges": [
            {"source": "api-pedidos", "target": "rabbitmq", "call_type": "async"},
            {"source": "rabbitmq", "target": "worker-notificacao", "call_type": "async"}
        ]
    })

    result = simulate_unavailability(arch, unavailable_node_id="worker-notificacao")

    # Asserções Matemáticas
    assert len(result["load_amplifications"]) == 0 # Sem retry storm
    assert "retidas na fila/tópico" in result["timeouts_exceeded"][0]
    
    # Raio de impacto isolado apenas ao worker
    assert "worker-notificacao" in result["blast_radius_impacted_nodes"]
    assert "api-pedidos" not in result["blast_radius_impacted_nodes"]

# ==========================================
# CENÁRIO 3: MULTIPLICADOR DE CARGA
# ==========================================
def test_load_multiplier_saturation():
    """
    Golden Test 3.1: Black Friday.
    Prova que a multiplicação da carga aciona o gatilho de saturação corretamente.
    """
    arch = SystemArchitecture(**{
        "system_name": "Carrinho",
        "nodes": [
            {"id": "carrinho", "replicas": 2, "max_rps_per_replica": 100.0}
        ],
        "edges": []
    })

    # Capacidade total = 200 RPS. Estado estacionário (50%) = 100 RPS. 
    # Multiplicador 5x = 500 RPS. Saturação = 500 / 200 = 2.5 (250%).
    result = simulate_load_multiplier(arch, multiplier=5.0)

    # Asserções Matemáticas
    assert result["node_saturations"]["carrinho"] == "250.0%"
    assert "abaixo da meta" in result["availability_impact"]
    assert "carrinho" in result["blast_radius_impacted_nodes"]

def test_load_multiplier_unrestricted_capacity():
    """
    Golden Test 3.2 (Corrigido): Pico Absorvido.
    Prova que componentes com capacidade nula (irrestrita) não saturam com multiplicadores.
    """
    arch = SystemArchitecture(**{
        "system_name": "Catalog Service",
        "nodes": [
            {"id": "catalog-api", "replicas": 10, "max_rps_per_replica": 50.0},
            {"id": "catalog-db", "replicas": 1, "max_rps_per_replica": None} # Capacidade infinita
        ],
        "edges": [
            {"source": "catalog-api", "target": "catalog-db", "call_type": "sync"}
        ]
    })

    # 10 * 50 = 500 RPS max. Base = 250 RPS. 2x = 500 RPS.
    result = simulate_load_multiplier(arch, multiplier=2.0)

    # catalog-api deve chegar a 100%, mas o DB (infinito) deve ficar em 0%
    assert result["node_saturations"]["catalog-api"] == "100.0%"
    assert result["node_saturations"]["catalog-db"] == "0.0%" # Sem falso positivo!
    