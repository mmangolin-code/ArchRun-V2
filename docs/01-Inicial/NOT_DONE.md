# O Que Ficou de Fora (Not Done)

Abaixo estão os itens deliberadamente omitidos deste ciclo de entrega de 15 horas e a justificativa técnica:

1. **Interface Gráfica Rica (Frontend):** Omitida para priorizar a solidez da fronteira determinística do motor e os testes de observabilidade. A interface fornecida é a documentação interativa Swagger/OpenAPI (`/docs`).
2. **Simulação de Monte Carlo para Latência Flutuante:** Omitida em favor de equações analíticas em estado estacionário, conforme permitido no escopo (seção 4 do edital)[cite: 1].
3. **Suporte a Protocolos gRPC / WebSockets:** O modelo atual assume apenas requisições HTTP REST síncronas e Mensageria Assíncrona padrão.
4. **Autenticação e Multi-tenancy:** Declarados expressamente como fora do escopo no edital[cite: 1].
