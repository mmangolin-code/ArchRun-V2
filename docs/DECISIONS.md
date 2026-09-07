# Registro de Decisões de Arquitetura (ADR)

## 1. Problema e Fronteiras do Escopo
O objetivo do sistema é eliminar decisões de arquitetura baseadas unicamente em intuição durante reuniões técnicas, fornecendo simulações numéricas determinísticas. 
Decidimos **não resolver**: renderização de diagramas, autenticação, multi-tenancy e simulação dinâmica de eventos discretos estocásticos em tempo real.

## 2. Padrão Arquitetural e A Fronteira Inegociável do LLM
Adotamos o padrão **"Deterministic Shell, Probabilistic Core"**:
- **Papel do LLM (Núcleo Probabilístico):** Atua estritamente como um tradutor de Linguagem Natural (prosa ambígua) para o Modelo Formal (Grafo JSON) e como formatador final da explicação em linguagem natural.
- **Papel do Código (Casca Determinística):** Toda a matemática de propagação de latência, cálculo de RPS efetivo com retries, taxa de utilização/saturação e mapeamento do Raio de Impacto (Blast Radius) é executada por funções puras em Python. NENHUM número da resposta é produzido pelo LLM.

## 3. Abordagem de Modelagem e Matemática
Escolhemos **fórmulas analíticas de forma fechada em estado estacionário (steady state)**.
- **Por que não Monte Carlo / Teoria das Filas Avançada?** O orçamento de tempo do desafio (15h) e o limite explicito de grafos de até 15 nós justificam o modelo de forma fechada. Ele entrega determinismo perfeito, alta performance e testabilidade auditável.
- **Limites do Modelo:** Assume fluxo contínuo em estado estacionário, sem considerar sobreníveis transitórios de rajada (bursts) menores que a janela de amostragem.

## 4. O que quebra em um escopo 10x maior?
1. **Modelagem Analítica:** Sistemas com centenas de nós em topologia malhada síncrona/assíncrona exigirão simulação de eventos discretos (ex: SimPy) e Teoria das Filas M/M/k para avaliar distribuições de latência p99 e contenção de conexões em pool de banco de dados.
2. **Parsing do LLM:** Textos longos de centenas de páginas exigirão um pipeline RAG com extração em duas etapas para montagem do grafo.