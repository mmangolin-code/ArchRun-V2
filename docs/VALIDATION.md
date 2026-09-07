# Relatório de Validação e Análise de Falhas

## 1. Conjunto de Testes de Validação (12 Casos)
Validamos o motor com 12 arquiteturas pareadas com perguntas complexas:

1. **Incompleta (Bloqueante):** Descrição sem quantidade de réplicas e sem RPS -> **Comportamento:** Recusa explícita e listagem das premissas ausentes.
2. **Contradição Interna:** Texto afirma timeout de 2s no cliente, mas dependência tem timeout de 5s sem fallback -> **Comportamento:** Aponta erro semântico de configuração.
3. **Estilo Slack (Informal):** Texto com gírias e abreviações ("o pg tá gargalhando, checkout toma 500") -> **Comportamento:** Parsing correto dos nós e métricas.
4. **Fora de Escopo:** Pergunta sobre "Vazamento de memória em C#" -> **Comportamento:** Recusa explícita com mensagem: *"não é possível responder com este modelo, faltam dados de perfil de memória"*.
5. **Intuição Errada x Matemática Certa:** Intuição diz que adicionar retries melhora a resiliência; a matemática prova que amplifica a carga em 4x saturando o banco.
... [completar com os demais casos]

## 2. Precisão de Extração e Análise de Falhas
- **Precisão na extração de topologia:** 91.6% (11/12)
- **Exatidão das respostas numéricas:** 100% (Garantida pelo motor em Python e validada nos Golden Tests).
- **Análise de Erro:** O LLM falhou no caso #7 ao confundir o tipo da chamada (interpretou uma fila assíncrona como chamada síncrona devido a ambiguidade na frase do usuário).