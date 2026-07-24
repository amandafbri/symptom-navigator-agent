import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from .telemetry import log_intent_and_outcome, logger, PIIScrubber
from .database import db
from .guardrails import SafetyGuardrail, HumanInTheLoopHook

# ==========================================
# Explicit Pydantic Schemas (Input & Output)
# ==========================================

class SymptomAssessmentInput(BaseModel):
    symptoms: str = Field(
        ...,
        description="Descrição detalhada dos sintomas relatados pelo paciente. Exemplo: 'Estou com dor no dente e gengiva inchada'."
    )

class MedicalSpecialtyRecommendation(BaseModel):
    symptoms: str = Field(..., description="Os sintomas avaliados.")
    recommended_specialty: str = Field(..., description="A especialidade médica recomendada.")
    is_emergency: bool = Field(..., description="Indica se o caso é uma emergência grave.")
    urgency_level: str = Field(..., description="Nível de urgência: 'ROUTINE', 'URGENT', ou 'EMERGENCY'.")
    guidance_message: str = Field(..., description="Orientação ao paciente ou LLM sobre os próximos passos.")
    status: str = Field(default="success", description="Status da execução.")


class AvailabilityCheckInput(BaseModel):
    specialty: str = Field(
        ...,
        description="A especialidade médica desejada (ex: 'Cardiologista', 'Ortopedista', 'Clínico Geral')."
    )
    desired_date: str = Field(
        ...,
        description="A data da consulta no formato estrito 'AAAA-MM-DD' (ex: '2026-06-15')."
    )

class TimeSlot(BaseModel):
    slot_id: str = Field(..., description="Identificador único da vaga.")
    time: str = Field(..., description="Horário da consulta (ex: '09:00').")
    doctor: str = Field(..., description="Nome do médico responsável.")

class AvailabilityCheckOutput(BaseModel):
    specialty: str = Field(..., description="Especialidade consultada.")
    date: str = Field(..., description="Data consultada.")
    available_slots: List[TimeSlot] = Field(default_factory=list, description="Lista de horários e vagas disponíveis.")
    status: str = Field(default="success", description="Status da consulta.")
    error_recovery_hint: Optional[str] = Field(default=None, description="Instruções para correção se algo falhar.")


class AppointmentBookingInput(BaseModel):
    patient_id: str = Field(
        ...,
        description="Identificador único do paciente (ex: Nome Completo ou CPF)."
    )
    slot_id: str = Field(
        ...,
        description="O código/ID único do horário escolhido (retornado pelo check_medical_specialty_availability)."
    )
    specialty: str = Field(
        ...,
        description="A especialidade médica para o agendamento."
    )
    date: str = Field(
        ...,
        description="A data da consulta no formato 'AAAA-MM-DD'."
    )
    doctor_name: str = Field(
        default="Médico Responsável",
        description="Nome do médico para a consulta."
    )
    confirmed_by_patient: bool = Field(
        default=True,
        description="Confirmação explícita obtida diretamente do paciente para efetivar a marcação (Human-in-the-Loop)."
    )

class AppointmentBookingOutput(BaseModel):
    appointment_id: Optional[str] = Field(default=None, description="ID único do agendamento finalizado.")
    status: str = Field(..., description="Status do agendamento ('confirmed', 'error', 'awaiting_confirmation').")
    patient_id: str = Field(..., description="Identificador do paciente.")
    slot_id: str = Field(..., description="Slot agendado.")
    message: str = Field(..., description="Mensagem de confirmação ou erro explicativo.")
    error_recovery_hint: Optional[str] = Field(default=None, description="Dica de recuperação de erro para a LLM.")


# ==========================================
# Tool Implementations with Guided Errors
# ==========================================

@log_intent_and_outcome("assess_symptoms_and_recommend_specialty")
def assess_symptoms_and_recommend_specialty(symptoms: str) -> Dict[str, Any]:
    """Avalia os sintomas relatados pelo paciente, verifica red lines de emergência e recomenda a especialidade médica adequada.

    Args:
        symptoms: Descrição detalhada dos sintomas relatados pelo paciente (ex: 'Dor de dente', 'Visão embaçada').

    Returns:
        Um dicionário contendo a especialidade recomendada, nível de urgência e orientações para o próximo passo.

    Guided Error Recovery:
        Se a entrada for vazia ou incompreensível, a ferramenta retornará uma dica instruindo a LLM a solicitar mais detalhes ao paciente.
    """
    if not symptoms or not isinstance(symptoms, str) or len(symptoms.strip()) < 2:
        return SymptomAssessmentOutput(
            symptoms=str(symptoms),
            recommended_specialty="Clínico Geral",
            is_emergency=False,
            urgency_level="ROUTINE",
            guidance_message="Descrição de sintomas muito curta. Por favor solicite mais detalhes ao paciente.",
            status="error"
        ).dict()

    # 1. Safety Guardrail Check (Emergency Red Lines)
    is_emergency, emergency_payload = SafetyGuardrail.evaluate_symptoms_safety(symptoms)
    if is_emergency and emergency_payload:
        return {
            "symptoms": symptoms,
            "recommended_specialty": "Pronto-Socorro / Emergência",
            "is_emergency": True,
            "urgency_level": "EMERGENCY",
            "guidance_message": emergency_payload["message"],
            "status": "EMERGENCY_RED_LINE"
        }

    # 2. Rule-based clinical specialty mapping
    symptoms_lower = symptoms.lower()
    if any(word in symptoms_lower for word in ["peito", "coração", "pressão alta", "palpitação"]):
        specialty = "Cardiologista"
        urgency = "URGENT"
    elif any(word in symptoms_lower for word in ["osso", "fratura", "costas", "joelho", "torção", "coluna", "articulação"]):
        specialty = "Ortopedista"
        urgency = "ROUTINE"
    elif any(word in symptoms_lower for word in ["dente", "boca", "gengiva", "siso"]):
        specialty = "Dentista"
        urgency = "ROUTINE"
    elif any(word in symptoms_lower for word in ["olho", "visão", "enxergar", "astigmatismo"]):
        specialty = "Oftalmologista"
        urgency = "ROUTINE"
    elif any(word in symptoms_lower for word in ["pele", "alergia", "coceira", "mancha", "espinha"]):
        specialty = "Dermatologista"
        urgency = "ROUTINE"
    else:
        specialty = "Clínico Geral"
        urgency = "ROUTINE"

    return MedicalSpecialtyRecommendation(
        symptoms=symptoms,
        recommended_specialty=specialty,
        is_emergency=False,
        urgency_level=urgency,
        guidance_message=f"Especialidade recomendada: {specialty}. O próximo passo é perguntar a data desejada para a consulta.",
        status="success"
    ).model_dump()


@log_intent_and_outcome("check_medical_specialty_availability")
def check_medical_specialty_availability(specialty: str, desired_date: str) -> Dict[str, Any]:
    """Consulta a lista de vagas e horários disponíveis na clínica para uma determinada especialidade médica e data.

    Args:
        specialty: Nome exato da especialidade médica (ex: 'Cardiologista', 'Ortopedista', 'Dentista').
        desired_date: Data no formato estrito 'AAAA-MM-DD' (ex: '2026-06-15').

    Returns:
        Um dicionário com a lista de horários/slots disponíveis (slot_id, horário, nome do médico).

    Guided Error Recovery:
        Em caso de formato de data inválido, a ferramenta retorna o erro sem crashar e orienta a LLM a solicitar o formato AAAA-MM-DD.
    """
    # Validation & Guided Error Handling for Date Format
    try:
        parsed_date = datetime.datetime.strptime(desired_date, "%Y-%m-%d")
    except ValueError:
        logger.warning(f"[GUIDED_ERROR] Invalid date format received: '{desired_date}'")
        return {
            "specialty": specialty,
            "date": desired_date,
            "available_slots": [],
            "status": "error",
            "error_recovery_hint": (
                f"Formato de data inválido ('{desired_date}'). "
                "Por favor solicite ao paciente que informe a data no formato AAAA-MM-DD (ex: 2026-06-15)."
            )
        }

    # Fetch persistent availability from Database
    slots_data = db.get_available_slots(specialty=specialty, date=desired_date)
    slots = [TimeSlot(**s) for s in slots_data]

    return AvailabilityCheckOutput(
        specialty=specialty,
        date=desired_date,
        available_slots=slots,
        status="success"
    ).model_dump()


@log_intent_and_outcome("book_medical_appointment")
def book_medical_appointment(
    patient_id: str,
    slot_id: str,
    specialty: str,
    date: str,
    doctor_name: str = "Dr. Silva",
    confirmed_by_patient: bool = True
) -> Dict[str, Any]:
    """Efetiva a marcação final da consulta médica para o paciente no slot selecionado e salva no banco de dados.

    Args:
        patient_id: Identificador único do paciente (ex: Nome Completo ou CPF).
        slot_id: O identificador único do horário retornado pelo check_medical_specialty_availability.
        specialty: A especialidade médica agendada.
        date: A data no formato 'AAAA-MM-DD'.
        doctor_name: O nome do médico escolhido.
        confirmed_by_patient: Confirmação humana explícita do paciente para o agendamento (Padrão: True).

    Returns:
        Um dicionário com o status do agendamento e o ID de confirmação.

    Guided Error Recovery:
        Se faltar a confirmação humana (HITL) ou se o patient_id for inválido, a ferramenta fornece orientação clara de recuperação.
    """
    # 1. Human-in-the-Loop Gatekeeper Check
    is_approved, hitl_error = HumanInTheLoopHook.verify_booking_confirmation(
        patient_id=patient_id,
        slot_id=slot_id,
        confirmed_by_patient=confirmed_by_patient
    )
    if not is_approved and hitl_error:
        return AppointmentBookingOutput(
            status="error",
            patient_id=patient_id,
            slot_id=slot_id,
            message=hitl_error["message"],
            error_recovery_hint="Pergunte ao paciente se ele confirma a marcação do horário antes de rechamar a ferramenta com confirmed_by_patient=True."
        ).model_dump()

    # 2. Input Validation
    if not patient_id or len(patient_id.strip()) < 2:
        return AppointmentBookingOutput(
            status="error",
            patient_id=str(patient_id),
            slot_id=slot_id,
            message="Identificador de paciente inválido.",
            error_recovery_hint="Por favor solicite o nome completo ou CPF do paciente para concluir o agendamento."
        ).model_dump()

    # 3. Persist booking in Database
    booking_res = db.book_slot(
        patient_id=patient_id,
        slot_id=slot_id,
        specialty=specialty,
        date=date,
        doctor_name=doctor_name
    )

    # Clean PII from returned confirmation message
    cleaned_patient_id = PIIScrubber.redact(patient_id)
    
    return AppointmentBookingOutput(
        appointment_id=booking_res["appointment_id"],
        status="confirmed",
        patient_id=cleaned_patient_id,
        slot_id=slot_id,
        message=f"Consulta agendada com sucesso! Código de Confirmação: {booking_res['appointment_id']} para o paciente '{cleaned_patient_id}' no slot '{slot_id}' com {doctor_name}."
    ).model_dump()
