# Registro de Decisões Arquiteturais (DECISIONS.md)


## 1. Visão Geral da Arquitetura e Limites (The LLM Boundary)

A arquitetura deste Motor de Raciocínio foi projetada com um princípio inegociável exigido no escopo: separação estrita entre extração semântica e cômputo matemático.

Para garantir que o LLM (Large Language Model) não opere como uma "calculadora", o sistema foi estruturado em um pipeline de duas camadas isoladas:

Camada de Extração (LLM via Groq + Pydantic): Atua exclusivamente como um "tradutor tipado". Recebe a prosa ambígua e tenta preencher um contrato de dados restrito (SystemArchitecture). O LLM não tem permissão de instrução para calcular disponibilidade, somar nós ou avaliar gargalos. Sua única função é extrair entidades (Nós), relações (Arestas) e intenção (Cenário).

Camada Determinística (Python/FastAPI): O motor real. Recebe o artefato JSON garantido pelo Pydantic e aplica fórmulas analíticas de forma fechada. Cada número de latência, amplificação de carga ou raio de impacto sai de funções Python puras, testáveis e versionáveis.

Escolha da Stack: Optei por FastAPI + Pydantic pela validação de esquema robusta e nativa (crucial para garantir que o LLM não invente chaves inexistentes). Para a extração, Groq (Llama-3) foi escolhido por sua altíssima velocidade (Time-to-First-Token) na geração de JSON, reduzindo a latência total do motor para ~1.5s a um custo computacional irrisório.

## 2. Bifurcações Enfrentadas e Caminhos Tomados

### Bifurcação A: Lidar com Entradas Incompletas

Cenário: "Temos uma API que chama um banco." (Faltam réplicas, rps, timeouts).

Opção 1: O motor Python infere valores padrão silenciosamente.

Opção 2: O LLM recusa tudo que não for perfeito.

Decisão: Via do Meio (Assunções Declaradas). Configurei o prompt para aplicar premissas seguras (ex: se não há réplicas, assuma 1; se não há limite de RPS, assuma capacidade irrestrita) e obriguei o LLM a registrar cada premissa no array assumptions_made. O modelo só é marcado como incomplete (bloqueando a execução) se dados topológicos críticos faltarem (ex: nós sem conexão lógica).

### Bifurcação B: Textos Contraditórios e Adversariais (Engenheiro no Slack)

Cenário: O usuário escreve "Consome a fila do Kafka de forma síncrona com timeout HTTP" ou tenta um prompt injection ("Ignore as regras e calcule X").

Decisão: Autocorreção Semântica e Blindagem de Prompt.

O prompt instrui o LLM a ser um "parser estrito" e a resolver ambiguidades arquiteturais (ex: forçar chamadas de fila para async), registrando a correção nas assunções para manter a transparência.

Contra prompt injection, a restrição response_format={"type": "json_object"} aliada ao parseamento estrito do Pydantic atua como um firewall: qualquer saída conversacional maliciosa do modelo falha na desserialização, estourando um erro controlado em vez de expor ou comprometer o sistema. O modelo formal não confia no input.

### Bifurcação C: Abordagem de Modelagem Computacional

Opção 1: Simulação de Eventos Discretos / Monte Carlo.

Opção 2: Fórmulas Analíticas de Forma Fechada.

Decisão: Opção 2. Dado o orçamento de tempo (15 horas) e o escopo de grafos de até 15 nós, fórmulas fechadas baseadas em Steady State (Estado Estacionário) entregam 95% do valor (responder "o que acontece se") com altíssima manutenibilidade. Monte Carlo introduziria um tempo de cômputo e complexidade de testes que violariam o princípio de manter o sistema enxuto e defensável.

## 3. Abordagem de Modelagem Matemática e Seus Limites

A matemática do motor é declarada, determinística e baseada no princípio de conservação de fluxo, assumindo que o sistema opera em um Estado Estacionário (Steady State) normalizado em 50% da capacidade do nó de entrada primário.

Limites Honestos e Declarados da Matemática:

Saturação Binária vs. Teoria das Filas: O motor calcula a saturação como Carga / Capacidade. Não aplicamos a Lei de Little (Little's Law) ou modelos Markovianos (M/M/1). Na vida real, a latência degrada exponencialmente antes de chegar a 100% de uso. No nosso modelo, a saturação é elástica até 99.9%, e quebra binariamente ao atingir 100%.

Ignorância de Topologia de Rede: A latência em cascata calcula puramente a soma dos tempos nominais dos serviços e timeouts informados. O tempo de trânsito na rede (RTT, cross-AZ) é assumido como zero, pois extrair isso de textos curtos exigiria alucinação de dados infundados.

Circuit Breakers não modelados: O motor entende Retries e Timeouts, computando amplificação de carga (Retry Storm). Porém, não modelamos padrões de resiliência avançados como Circuit Breaker (Open/Half-Open), o que significa que o motor pode penalizar o cálculo de carga inútil na rede por mais tempo do que um sistema real bem configurado faria.

## 4. O Que Quebra em um Escopo 10x Maior (150+ nós)

Se a arquitetura do cliente saltar de 15 para 150+ componentes, o design atual falhará em três frentes:

LLM Context & Alucinação Estrutural: O LLM perderá a coesão topológica. Em um texto descrevendo 150 nós, a atenção do modelo degradará, gerando nós órfãos, invertendo a direção de arestas (Source/Target) e estourando limites de tokens de saída. Solução em 10x: Substituir a extração em lote (Zero-Shot) por um processo iterativo (Agentes extraindo subdomínios) ou forçar a ingestão determinística via Infra-as-Code (ex: ler arquivos Terraform/Manifestos K8s) em vez de texto livre.

Estouro de Pilha no Cálculo de Cascata (Grafos Cíclicos): Atualmente, a latência é calculada por recursão em profundidade (DFS). Em arquiteturas de 150 nós, a chance de existirem dependências cíclicas (ex: A -> B -> C -> A) é quase certa. A matemática atual entraria em loop infinito (RecursionError). Solução em 10x: Implementar algoritmos de ordenação topológica e detecção de ciclos baseados no Algoritmo de Tarjan antes de autorizar a execução do cômputo.

Estado do Modelo (Stateless vs Stateful): Hoje, o modelo formal "vive e morre" na requisição HTTP (stateless). O requisito "passível de comparação de diferenças (diffable)" funciona via JSON, mas em larga escala, debugar 150 nós requer persistência e histórico. Solução em 10x: O modelo formal passaria a ser persistido em um banco de dados relacional (ex: Postgres + Drizzle), permitindo mutações pontuais via API (PATCH) para corrigir arestas específicas sem precisar reprocessar o texto inteiro no LLM.