import pytest
from app.schemas import SystemArchitecture, Node, Edge
from app.engine.scenario import simulate_latency_degradation
from app.engine.calculator import calculate_effective_rps, calculate_node_saturation

def test_golden_postgres_latency_degradation():
    """
    GOLDEN TEST 1: Degradação de Latência no Postgres
    
    DERIVAÇÃO MANUAL:
    1. Carga inicial: Checkout (6 réplicas * 80 rps = 480 cap), Pricing (4 réplicas * 80 rps = 320 cap).
    2. Carga de entrada testada: 320 rps.
    3. Latência acumulada: Base Checkout (50ms) + Base Pricing (50ms) + Postgres Degradado (3000ms) = 3050ms.
    4. Avaliação de Timeout: 3050ms > Timeout Checkout->Pricing (2000ms) -> ESTOURO DE TIMEOUT.
    5. Amplificação por Retries: 3 retries na borda -> Carga amplificada = 320 * (1 + 3) = 1280 rps.
    6. Saturação do Pricing: 1280 / (4 * 80) = 1280 / 320 = 4.0 (100% de saturação no limite da capacidade).
    7. Blast Radius: Checkout e Pricing afetados -> 2 de 4 componentes.
    """
    arch = SystemArchitecture(
        nodes=[
            Node(id="checkout", replicas=6, max_rps_per_replica=80.0, timeout_ms=2000.0),
            Node(id="pricing", replicas=4, max_rps_per_replica=80.0, timeout_ms=2000.0),
            Node(id="postgres-primary", replicas=1, max_rps_per_replica=500.0, timeout_ms=None),
            Node(id="faturamento-worker", replicas=1, max_rps_per_replica=None, timeout_ms=None)
        ],
        edges=[
            Edge(source="checkout", target="pricing", call_type="sync", retries=3, timeout_ms=2000.0),
            Edge(source="pricing", target="postgres-primary", call_type="sync", retries=0, timeout_ms=None),
            Edge(source="checkout", target="faturamento-worker", call_type="async", retries=0, timeout_ms=None)
        ],
        target_availability=0.999
    )

    result = simulate_latency_degradation(arch, degraded_node_id="postgres-primary", degraded_latency_ms=3000.0, input_rps=320.0)

    # Asserções Determinísticas
    assert len(result["timeouts_exceeded"]) == 1
    assert "3050.0ms" in result["timeouts_exceeded"][0]
    assert "4x" in result["load_amplifications"][0]
    assert "1280" in result["load_amplifications"][0]
    assert len(result["blast_radius_impacted_nodes"]) == 2
    assert "checkout" in result["blast_radius_impacted_nodes"]
    assert "pricing" in result["blast_radius_impacted_nodes"]

def test_golden_effective_rps_calculation():
    """GOLDEN TEST 2: Cálculo isolado da fórmula de amplificação de retries."""
    # Base: 100 rps com 3 retries em falha -> 100 * (1 + 3) = 400 rps
    rps_falha = calculate_effective_rps(base_rps=100.0, retries=3, target_failing=True)
    assert rps_falha == 400.0

    # Base: 100 rps sem falha -> 100 rps
    rps_sucesso = calculate_effective_rps(base_rps=100.0, retries=3, target_failing=False)
    assert rps_sucesso == 100.0

def test_golden_saturation_calculation():
    """GOLDEN TEST 3: Cálculo isolado da taxa de saturação."""
    # Carga de 320 rps em 4 réplicas de 80 rps -> 320 / 320 = 1.0 (100%)
    sat = calculate_node_saturation(effective_rps=320.0, replicas=4, max_rps_per_replica=80.0)
    assert sat == 1.0