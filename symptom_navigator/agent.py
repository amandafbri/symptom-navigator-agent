from functools import cached_property                                                                                                                                                                           
from google.adk.agents.llm_agent import Agent                                                                                                                                                                   
from google.adk.models import Gemini                                                                                                                                                                            
from google.genai import Client                                                                                                                                                                                 
from . import tools                                                                                                                                                                                             
                                                                                                                                                                                                                    
# Cria uma classe customizada para forçar a região global no Gemini                                                                                                                                             
class GlobalGemini(Gemini):                                                                                                                                                                                     
    @cached_property                                                                                                                                                                                              
    def api_client(self) -> Client:                                                                                                                                                                               
        # Inicializa o cliente do GenAI SDK apontando para a região global no Vertex AI                                                                                                                             
        return Client(vertexai=True, location="global")                                                                                                                                                             
  
# Define o agente usando a classe customizada
root_agent = Agent(
    model=GlobalGemini(model='gemini-3.1-flash-lite'),
    name='symptom_navigator_agent',
    description='Assistente de Triagem e Direcionamento Médico (Symptom Navigator)',
    instruction="""Você é o Symptom Navigator, um assistente virtual simpático e prestativo para um portal de clínicas médicas. 
Seu objetivo é ajudar pacientes a triar seus sintomas, direcioná-los para a especialidade médica adequada e realizar o agendamento de consultas.

Siga rigorosamente estes passos para interagir com o usuário:
1. Peça para o paciente descrever os sintomas que está sentindo, caso ele ainda não o tenha feito.
2. Com base nos sintomas descritos, use a ferramenta `match_symptoms_to_specialty` para identificar a especialidade médica recomendada.
3. Informe ao paciente a especialidade identificada e pergunte para qual data ele gostaria de verificar a disponibilidade de consultas (no formato AAAA-MM-DD).
4. Use a ferramenta `check_availability` com a especialidade e a data fornecidas para buscar os horários disponíveis.
5. Apresente os horários disponíveis (slots), os nomes dos médicos e peça para o paciente escolher um dos slots (fornecendo o slot_id ou horário) e informar seu nome completo ou identificador único.
6. Use a ferramenta `book_appointment` com o identificador do paciente e o slot_id selecionado para efetivar a marcação da consulta.
7. Confirme os detalhes do agendamento finalizado de forma clara.

Lembre-se de ser empático, atencioso e falar sempre em português.""",
    tools=[
        tools.match_symptoms_to_specialty,
        tools.check_availability,
        tools.book_appointment,
    ]
)
