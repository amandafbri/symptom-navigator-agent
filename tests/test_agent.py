import os
import json
import pytest
from symptom_navigator.tools import (
    assess_symptoms_and_recommend_specialty,
    check_medical_specialty_availability,
    book_medical_appointment
)
from symptom_navigator.guardrails import SafetyGuardrail, HumanInTheLoopHook
from symptom_navigator.telemetry import PIIScrubber

def load_golden_dataset():
    path = os.path.join(os.path.dirname(__file__), "golden_dataset.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

# ==========================================
# 1. Safety Red Line & Guardrail Tests
# ==========================================
def test_emergency_red_line_guardrail():
    symptoms = "Estou com dor no peito insuportável e formigamento no braço"
    is_emergency, payload = SafetyGuardrail.evaluate_symptoms_safety(symptoms)
    assert is_emergency is True
    assert payload["status"] == "EMERGENCY_RED_LINE"
    assert "Pronto-Socorro" in payload["message"] or "SAMU" in payload["message"]

def test_symptom_triage_emergency_tool():
    res = assess_symptoms_and_recommend_specialty("Dor forte no peito e formigamento")
    assert res["is_emergency"] is True
    assert res["status"] == "EMERGENCY_RED_LINE"

# ==========================================
# 2. Tool & Interface Design Tests
# ==========================================
def test_symptom_triage_dentist():
    res = assess_symptoms_and_recommend_specialty("Dor de dente e gengiva inchada")
    assert res["recommended_specialty"] == "Dentista"
    assert res["is_emergency"] is False

def test_availability_check_valid_date():
    res = check_medical_specialty_availability("Dentista", "2026-06-15")
    assert res["status"] == "success"
    assert len(res["available_slots"]) > 0

def test_availability_check_invalid_date_guided_error():
    res = check_medical_specialty_availability("Dentista", "15-06-2026")
    assert res["status"] == "error"
    assert "error_recovery_hint" in res
    assert "AAAA-MM-DD" in res["error_recovery_hint"]

# ==========================================
# 3. Human-in-the-Loop & Booking Tests
# ==========================================
def test_booking_without_hitl_confirmation():
    is_approved, error = HumanInTheLoopHook.verify_booking_confirmation(
        patient_id="Carlos Silva",
        slot_id="dentista_slot_1",
        confirmed_by_patient=False
    )
    assert is_approved is False
    assert error["status"] == "AWAITING_HUMAN_CONFIRMATION"

def test_booking_with_hitl_confirmation():
    res = book_medical_appointment(
        patient_id="Carlos Silva",
        slot_id="dentista_slot_1",
        specialty="Dentista",
        date="2026-06-15",
        confirmed_by_patient=True
    )
    assert res["status"] == "confirmed"
    assert "appointment_id" in res

# ==========================================
# 4. PII Redaction Tests
# ==========================================
def test_pii_redaction():
    text_with_cpf = "O paciente com CPF 123.456.789-00 e email teste@email.com solicitou agendamento."
    redacted = PIIScrubber.redact(text_with_cpf)
    assert "123.456.789-00" not in redacted
    assert "[REDACTED_CPF]" in redacted
    assert "[REDACTED_EMAIL]" in redacted
