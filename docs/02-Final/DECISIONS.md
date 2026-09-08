# Registro de Decisões Arquiteturais (DECISIONS.md)

## 1. Visão Geral da Arquitetura
A arquitetura deste motor de raciocínio baseia-se em um princípio inegociável: **separação estrita entre extração semântica e cômputo matemático**. O sistema foi desenhado em duas camadas principais:
1.  **Parser (LLM - Groq):** Atua exclusivamente como um tradutor de linguagem natural para um modelo formal (JSON). Ele não calcula, não infere disponibilidade e não avalia saturação.
2.  **Engine Determinística (Python/FastAPI):** Recebe o modelo formal tipado (Pydantic) e aplica fórmulas analíticas de forma fechada para calcular latência, saturação, amplificação de carga e raio de impacto.

Essa abordagem garante que as saídas numéricas sejam 100% testáveis, previsíveis e independentes das alucinações inerentes aos modelos de linguagem.

## 2. Bifurcações Enfrentadas e Caminhos Escolhidos

### Bifurcação A: Lidar com Dados Ausentes (Incompletos)
*   **Opção 1:** Fazer o motor de cálculo Python deduzir dados.
*   **Opção 2:** Fazer o LLM assumir premissas arquiteturais seguras e registrá-las.
*   **Decisão:** Escolhi a **Opção 2**. Desenvolvi no `SYSTEM_PROMPT` uma regra para "Assunções Seguras". Se o usuário omite réplicas, o LLM assume 1 e registra em `assumptions_made`. Isso mantém o contrato transparente. Caso a omissão seja crítica (ex: nenhum nó de origem), o status muda para `incomplete` e o sistema recusa o cálculo graciosamente.

### Bifurcação B: Abordagem de Modelagem Computacional
*   **Opção 1:** Simulação de Eventos Discretos / Teoria das Filas (Modelos Markovianos).
*   **Opção 2:** Fórmulas Analíticas de Forma Fechada (Cálculo de Saturação e Cascata).
*   **Decisão:** Escolhi a **Opção 2**. Para o escopo de 3 dias e grafos de até 15 nós, fórmulas fechadas em estado estacionário (*steady state*) oferecem precisão suficiente para responder a perguntas de "o que acontece se" sem a complexidade computacional e o tempo de desenvolvimento de um simulador de eventos discretos.

## 3. Abordagem de Modelagem e Seus Limites
O modelo opera sob a premissa de **estado estacionário (Steady State)**. Para cenários de multiplicador de carga, assumimos que o sistema normalmente opera a 50% de sua capacidade limite do nó de entrada.

**Limites Claros do Modelo:**
*   **Sem Teoria das Filas:** Não modelamos o acúmulo temporal de requisições (Little's Law). A saturação é vista de forma binária (utilização instantânea).
*   **Latência de Rede:** Ignorada. O cálculo foca no tempo de processamento das dependências.
*   **Ciclos Infinitos:** O cálculo de cascata de latência assume Grafos Direcionados Acíclicos (DAGs). Dependências cíclicas não são mitigadas matematicamente nesta versão.

## 4. O Que Quebra em um Escopo 10x Maior (150+ nós)
Se a arquitetura escalasse para 150 nós, dois componentes críticos quebrariam:
1.  **LLM Context Window & JSON Structure:** A janela de contexto do LLM sofreria para manter a coerência das ligações (arestas) em um texto enorme, aumentando a chance de criar nós "fantasmas" ou esquecer conexões. A taxa de extração correta cairia drasticamente.
2.  **Cálculo de Latência (Recursão):** A busca em profundidade recursiva para calcular a latência em cascata (`calculate_cascade_latency`) sofreria degradação de performance e risco de `RecursionError` caso o grafo de 150 nós apresentasse rotas circulares complexas.