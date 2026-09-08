# O Que Ficou de Fora e o Porquê (NOT_DONE.md)

Dada a restrição orçamentária de tempo (3 dias / ~15 horas) e a premissa de que "um modelo simples com fronteiras honestas supera um elaborado que mente", optei por deixar os seguintes itens fora do escopo do motor atual:

## 1. Teoria das Filas Avançada (Modelos Markovianos)
*   **O que não foi feito:** O cálculo de saturação baseia-se puramente na utilização (RPS / Capacidade). Não apliquei fórmulas M/M/1 ou M/M/c para calcular como a latência cresce exponencialmente à medida que a utilização se aproxima de 100%.
*   **Por quê:** Inserir teoria das filas exigiria que o usuário fornecesse ou que o LLM "chutasse" tempos médios de serviço (`mu`) e variância de chegada de requisições. O risco de alucinação aumentaria drasticamente. A métrica binária de saturação cumpre o objetivo de apontar gargalos críticos com mais honestidade baseada nos dados disponíveis.

## 2. Detecção de Ciclos no Grafo (Deadlocks Arquiteturais)
*   **O que não foi feito:** O parser extrai o grafo e a engine calcula o caminho, mas não há um validador algorítmico (ex: DFS de detecção de ciclo) para impedir um loop infinito (Serviço A chama B, que chama A).
*   **Por quê:** Em 15 horas, priorizei cobrir os três cenários exigidos (degradação, indisponibilidade, carga) de forma ponta-a-ponta. Arquiteturas descritas em parágrafos simples raramente contêm ciclos fechados explícitos comparados a diagramas corporativos complexos.

## 3. Latência de Rede Inter-Componentes
*   **O que não foi feito:** A latência em cascata considera apenas o tempo nominal reportado no cenário, ignorando os RTTs (Round Trip Times) da infraestrutura de rede.
*   **Por quê:** Informações sobre topologia de rede (se dois serviços estão na mesma AZ ou em continentes diferentes) nunca estão presentes em descrições casuais ("engenheiro real no Slack"). Computar a latência da rede exigiria inventar dados, violando a regra n° 2 do desafio.

## 4. Renderização Visual e UI
*   **O que não foi feito:** Não há frontend em React/Next.js para renderizar o grafo extraído.
*   **Por quê:** O edital é claro: *“Três coisas em padrão de produção superam dez apenas rascunhadas”*. O esforço foi 100% investido em robustecer o motor determinístico em Python e os *golden tests*, deixando o serviço disponível via FastAPI de forma confiável.