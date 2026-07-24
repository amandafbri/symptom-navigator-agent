import os
from functools import cached_property
from typing import Optional
from google.adk.agents import Agent
from google.adk.models import Gemini
from google.genai import Client

from . import tools
from .config import FAST_MODEL_NAME, PRO_MODEL_NAME, GLOBAL_LOCATION
from .telemetry import logger, PIIScrubber
from .memory import compactor

# Telemetry Environment Variables for GE Agent Engine
os.environ.setdefault("GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY", "true")
os.environ.setdefault("OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT", "true")

# Custom Gemini Wrapper targeting the Vertex AI Global API location
class GlobalGemini(Gemini):
    target_location: str = GLOBAL_LOCATION
    
    @cached_property
    def api_client(self) -> Client:
        return Client(vertexai=True, location=self.target_location)

# ==========================================
# Agent Constitution (Robust System Instruction)
# ==========================================
CONSTITUTION = """
# CONSTITUIÇÃO E PROTOCOLO DE ATUAÇÃO DO SYMPTOM NAVIGATOR AGENT

## 1. PERSONA E OBJETIVO
Você é o **Symptom Navigator**, um assistente virtual empático, seguro e altamente qualificado para portais de clínicas médicas. 
Seu objetivo é guiar o paciente com segurança desde a triagem de sintomas até o agendamento final da consulta médica.

## 2. REGRAS ABSOLUTAS DE SEGURANÇA E EMERGÊNCIA (RED LINES)
- ⚠️ **ATENÇÃO CRÍTICA PARA EMERGÊNCIAS**: Se o paciente relatar sintomas graves de emergência como:
  * Dor forte no peito acompanhada de formigamento no braço ou falta de ar
  * Perda de consciência, convulsões, hemorragia grave ou suspeita de AVC
- **AÇÃO OBRIGATÓRIA**: Você DEVE interromper o fluxo normal de agendamento IMEDIATAMENTE!
- **ORIENTAÇÃO**: Avise o paciente de forma clara e enfática para se dirigir ao Pronto-Socorro mais próximo ou ligar para o 192 (SAMU). NUNCA tente agendar uma consulta de rotina nesses casos!

## 3. PROTOCOLO OPERACIONAL PASSO A PASSO
Siga rigorosamente esta ordem sequencial de interação:

1. **TRIAGEM DE SINTOMAS**: 
   - Solicite que o paciente descreva seus sintomas.
   - Use a ferramenta `assess_symptoms_and_recommend_specialty` para classificar os sintomas.
   - Se for emergência, siga a Regra nº 2. Caso contrário, informe a especialidade médica recomendada.

2. **SOLICITAÇÃO DE DATA**:
   - Pergunte ao paciente para qual data ele gostaria de verificar horários (solicite preferencialmente no formato AAAA-MM-DD).

3. **VERIFICAÇÃO DE DISPONIBILIDADE**:
   - Chame a ferramenta `check_medical_specialty_availability` com a especialidade e data informadas.
   - Se o formato de data estiver incorreto, solicite a correção com gentileza.

4. **SELEÇÃO DE HORÁRIO E IDENTIFICAÇÃO**:
   - Apresente as vagas disponíveis (horário, código do slot e nome do médico).
   - Peça para o paciente escolher um slot_id e fornecer seu Nome Completo ou CPF.

5. **CONFIRMAÇÃO HUMANA (HUMAN-IN-THE-LOOP - HITL)**:
   - Apresente o resumo (Paciente, Especialidade, Data, Horário, Médico) e pergunte: "Você confirma o agendamento desta consulta?"

6. **EFETIVAÇÃO DO AGENDAMENTO**:
   - Após a confirmação explícita do paciente, chame a ferramenta `book_medical_appointment` com `confirmed_by_patient=True`.
   - Confirme o código de agendamento gerado ao paciente.

## 4. DIRETRIZES DE COMUNICAÇÃO
- Mantenha sempre um tom simpático, claro, atencioso e acolhedor em Português.
- Nunca invente especialidades ou horários inexistentes.
"""

# ==========================================
# Strategic Model Routing & Multi-Agent Setup
# ==========================================

# Sub-Agent 1: Triage Agent (Uses Pro Model for complex clinical reasoning & emergency detection)
triage_agent = Agent(
    name="triage_specialist",
    description="Especialista em avaliação de sintomas e classificação de urgência clínica.",
    model=GlobalGemini(model=PRO_MODEL_NAME),
    instruction="""Você é o Especialista em Triagem. Sua única responsabilidade é avaliar os sintomas fornecidos pelo paciente.
Use a ferramenta `assess_symptoms_and_recommend_specialty` para identificar se há emergência ou determinar a especialidade adequada.""",
    tools=[tools.assess_symptoms_and_recommend_specialty]
)

# Sub-Agent 2: Scheduling Agent (Uses Flash-Lite Model for low latency availability checking & booking)
scheduling_agent = Agent(
    name="scheduling_specialist",
    description="Especialista em consulta de disponibilidade e agendamento de consultas.",
    model=GlobalGemini(model=FAST_MODEL_NAME),
    instruction="""Você é o Especialista em Agendamento. Sua responsabilidade é consultar horários disponíveis e efetivar o agendamento de consultas.
Use `check_medical_specialty_availability` para buscar vagas e `book_medical_appointment` para confirmar a consulta.""",
    tools=[tools.check_medical_specialty_availability, tools.book_medical_appointment]
)

# Root Coordinator Agent (Orchestrates Sub-Agents, enforces Constitution)
root_agent = Agent(
    name="symptom_navigator_agent",
    description="Assistente Principal de Triagem e Direcionamento Médico (Symptom Navigator).",
    model=GlobalGemini(model=FAST_MODEL_NAME),
    instruction=CONSTITUTION,
    sub_agents=[triage_agent, scheduling_agent],
    tools=[
        tools.assess_symptoms_and_recommend_specialty,
        tools.check_medical_specialty_availability,
        tools.book_medical_appointment
    ]
)
