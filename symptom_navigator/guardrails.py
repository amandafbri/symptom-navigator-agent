from typing import Dict, Any, Tuple, Optional
from .telemetry import logger

# Red Line Emergency Keywords that require immediate Emergency Room (ER / Pronto-Socorro) redirection
EMERGENCY_RED_FLAGS = [
    "dor no peito",
    "formigamento no braço",
    "falta de ar severa",
    "perda de consciência",
    "convulsão",
    "hemorragia grave",
    "avc",
    "paralisia facial",
    "parada cardiorrespiratória",
    "infarto"
]

class SafetyGuardrail:
    """Guardrail to enforce clinical safety and emergency redirection red lines."""

    @staticmethod
    def evaluate_symptoms_safety(symptoms: str) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """Evaluates symptoms for life-threatening emergency indicators.
        
        Returns:
            (is_emergency, emergency_response_dict)
        """
        symptoms_lower = symptoms.lower()
        matched_flags = [flag for flag in EMERGENCY_RED_FLAGS if flag in symptoms_lower]
        
        # Check combination of critical indicators (e.g. chest pain + arm numbness)
        has_chest_pain = "peito" in symptoms_lower or "coração" in symptoms_lower or "infarto" in symptoms_lower
        has_arm_numbness = "braço" in symptoms_lower or "formigamento" in symptoms_lower or "dormência" in symptoms_lower
        
        if matched_flags or (has_chest_pain and has_arm_numbness):
            logger.warning(f"[GUARDRAIL_TRIGGERED] Emergency red line detected in symptoms: {symptoms}")
            return True, {
                "status": "EMERGENCY_RED_LINE",
                "is_emergency": True,
                "action_required": "REDIRECT_TO_ER",
                "message": (
                    "⚠️ ATENÇÃO: Os sintomas relatados (ex: dor no peito / formigamento) indicam uma POSSÍVEL EMERGÊNCIA MÉDICA GRAVE. "
                    "NÃO é seguro aguardar uma consulta de rotina! Por favor, dirija-se IMEDIATAMENTE ao Pronto-Socorro mais próximo "
                    "ou ligue para o SAMU (192)."
                )
            }
        return False, None


class HumanInTheLoopHook:
    """Human-in-the-loop (HITL) gatekeeper requiring explicit patient confirmation before finalizing booking."""

    @staticmethod
    def verify_booking_confirmation(patient_id: str, slot_id: str, confirmed_by_patient: bool) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """Validates explicit human approval before executing high-stakes appointment booking.
        
        Returns:
            (is_approved, error_dict)
        """
        if not confirmed_by_patient:
            logger.info(f"[HITL_GATE] Appointment booking paused awaiting human confirmation for patient '{patient_id}', slot '{slot_id}'.")
            return False, {
                "status": "AWAITING_HUMAN_CONFIRMATION",
                "requires_confirmation": True,
                "message": (
                    f"Confirmação necessária: Por favor solicite a confirmação explícita do paciente para o agendamento no slot '{slot_id}' "
                    f"para o paciente '{patient_id}' antes de chamar a ferramenta de efetivação final."
                )
            }
        return True, None
