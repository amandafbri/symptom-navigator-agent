# Symptom Navigator Agent (Assistente de Triagem e Direcionamento Médico)

Este repositório contém a implementação do **Symptom Navigator Agent**, um assistente virtual empático desenvolvido com a biblioteca `google-adk` para auxiliar pacientes em portais de clínicas médicas. O agente ajuda na triagem de sintomas, recomendação da especialidade médica adequada, consulta de horários disponíveis e efetivação do agendamento de consultas de forma totalmente conversacional.

O agente utiliza o modelo **Gemini 3.1 Flash Lite** (`gemini-3.1-flash-lite`) e é integrado ao Gemini Enterprise Agent Platform Agent Runtime para implantação em produção no Google Cloud.

---

## 📂 Estrutura do Repositório

O projeto possui a seguinte estrutura de arquivos:

*   symptom_navigator/: Módulo principal da aplicação.
    *   agent.py: Definição do agente, instruções de comportamento em português e configuração do cliente Gemini com região global da Agent Platform.
    *   tools.py: Implementação das ferramentas do agente (mapeamento de sintomas para especialidade, consulta de horários disponíveis e agendamento).
    *   .env: Arquivo de variáveis de ambiente locais.
*   deploy_agent.py: Script de implantação da aplicação no Google Cloud Agent Platform Agent Runtime.
*   requirements.txt: Dependências em Python exigidas pelo projeto.
*   README.md: Este arquivo explicativo do projeto.

---

## 🛠️ Ferramentas (Tools) Incorporadas

O agente conta com 3 ferramentas principais implementadas em `tools.py`:

1.  `match_symptoms_to_specialty`: Identifica a especialidade médica recomendada com base na descrição de sintomas do paciente.
2.  `check_availability`: Consulta a lista de horários (slots) e médicos disponíveis para uma determinada especialidade e data específica (`AAAA-MM-DD`).
3.  `book_appointment`: Efetiva e confirma o agendamento da consulta médica para o paciente no slot selecionado.

---

## ⚙️ Configurações Locais

As configurações e credenciais necessárias estão detalhadas no arquivo `.env`:

*   `GOOGLE_GENAI_USE_VERTEXAI`: Define o uso da GE Agent Platform (definido como `1`).
*   `GOOGLE_CLOUD_PROJECT`: ID do projeto Google Cloud.
*   `GOOGLE_CLOUD_LOCATION`: Região global para a API da GE Agent Platform.
*   `DEPLOY_LOCATION`: Região padrão onde o GE Agent Platform Agent Runtime será implantado (ex: `us-central1`).

---

## 🚀 Instalação e Execução Local

### 1. Requisitos Prévios
- Python 3.10 ou superior instalado.
- Conta do Google Cloud com GE Agent Platform habilitado.
- CLI do Google Cloud (`gcloud`) instalada e autenticada:
  ```bash
  gcloud auth application-default login
  ```

### 2. Configurando o Ambiente
Crie um ambiente virtual Python e instale todas as dependências:

```bash
# Criar ambiente virtual
python3 -m venv .venv

# Ativar ambiente virtual
source .venv/bin/activate

# Instalar dependências
pip install -r requirements.txt
```

---

## ☁️ Deploy no Agent Runtime

O script `deploy_agent.py` realiza o empacotamento das dependências, empacota o módulo `symptom_navigator` e implanta a aplicação no **Agent Runtime**.

Para rodar o deploy:

```bash
# Configurar as variáveis de ambiente necessárias (caso não use o .env ou queira sobrescrever)
export GOOGLE_CLOUD_PROJECT="seu-projeto-gcp"
export GCS_STAGING_BUCKET="gs://seu-bucket-de-staging"

# Executar o script de deploy
python deploy_agent.py
```

Uma vez finalizado, o script retornará a confirmação com o ID do recurso do agente implantado pronto para uso.
