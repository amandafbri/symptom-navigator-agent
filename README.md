# 🏥 Symptom Navigator Agent

Este repositório contém a implementação do **Symptom Navigator Agent**, um assistente virtual empático desenvolvido com a biblioteca `google-adk` para auxiliar pacientes em portais de clínicas médicas. O agente ajuda na triagem de sintomas, recomendação da especialidade médica adequada, consulta de horários disponíveis e efetivação do agendamento de consultas de forma totalmente conversacional.

---

## 📂 Estrutura Completa do Repositório

```
symptom-navigator-agent/
├── terraform/                  # Infraestrutura como Código (IaC)
│   ├── main.tf                 # Provisionamento de GCS, Secret Manager, Artifact Registry e IAM
│   ├── variables.tf            # Variáveis do Terraform
│   └── outputs.tf              # Saídas do Terraform
├── symptom_navigator/          # Módulo principal do Agente ADK
│   ├── __init__.py             # Inicialização do pacote
│   ├── agent.py                # Multi-Agent setup (Triage, Scheduling, Coordinator), Constituição e Roteamento
│   ├── tools.py                # Ferramentas Pydantic com Docstrings detalhadas e Guided Errors
│   ├── database.py             # Banco de dados SQLite persistente para agendamentos e sessões
│   ├── memory.py               # Compacção de histórico e consolidação de memória assíncrona
│   ├── guardrails.py           # Guardrails de emergência médica e Hook Human-in-the-Loop
│   ├── telemetry.py            # Logs JSON Estruturados, Intent vs Outcome, OpenTelemetry e Redação de PII
│   ├── secrets.py              # Injeção segura via Secret Manager
│   └── config.py               # Definições de Roteamento Estratégico de Modelos (Flash vs Pro)
├── tests/                      # Suíte de Testes e Avaliação Automatizada
│   ├── run_tests.py            # Executador de testes unitários e de integração (unittest)
│   ├── test_agent.py           # Casos de teste automatizados
│   └── golden_dataset.json     # Dataset dourado de testes de regressão
├── Dockerfile                  # Containerização para deploy no Cloud Run / Agent Engine
├── eval.py                     # Script de avaliação multi-turno com Vertex AI Evals
├── deploy_agent.py             # Script de implantação no Agent Engine (GE Agent Platform)
├── requirements.txt            # Dependências Python do projeto
└── README.md                   # Documentação detalhada e matriz de avaliação
```

---

## 💬 Execução Local Interativa (Chat no Terminal)

Para interagir com o agente diretamente pelo terminal:

### Chat Interativo no Terminal
```bash
.venv/bin/python3 chat_local.py
```

---

## 🧪 Execução dos Testes Automatizados (CI/CD)

Para rodar a suíte de testes automatizados e validar o comportamento das ferramentas, redação de PII, guardrails de emergência e hook HITL:

```bash
PYTHONPATH=. .venv/bin/python3 tests/run_tests.py
```

### Exemplo de Saída dos Testes:
```
Ran 8 tests in 0.015s
OK
```

---

## 🚀 Execução e Avaliação no Vertex AI Evals

Para executar a avaliação multi-turno contra o dataset de cenários de teste:

```bash
PYTHONPATH=. .venv/bin/python3 eval.py
```

---

## ☁️ Implantação da Infraestrutura (Terraform & Deploy)

### 1. Provisionar Infraestrutura com Terraform:
```bash
cd terraform
terraform init
terraform apply -auto-approve
cd ..
```

### 2. Implantar Agente no Agent Engine:
```bash
python3 deploy_agent.py
```
