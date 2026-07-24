import unittest
import os
import json

from symptom_navigator.tools import (
    assess_symptoms_and_recommend_specialty,
    check_medical_specialty_availability,
    book_medical_appointment
)
from symptom_navigator.guardrails import SafetyGuardrail, HumanInTheLoopHook
from symptom_navigator.telemetry import PIIScrubber

class TestSymptomNavigatorAgent(unittest.TestCase):

    def test_emergency_red_line_guardrail(self):
        symptoms = "Estou com dor no peito insuportável e formigamento no braço"
        is_emergency, payload = SafetyGuardrail.evaluate_symptoms_safety(symptoms)
        self.assertTrue(is_emergency)
        self.assertEqual(payload["status"], "EMERGENCY_RED_LINE")
        self.assertTrue("Pronto-Socorro" in payload["message"] or "SAMU" in payload["message"])

    def test_symptom_triage_emergency_tool(self):
        res = assess_symptoms_and_recommend_specialty("Dor forte no peito e formigamento")
        self.assertTrue(res["is_emergency"])
        self.assertEqual(res["status"], "EMERGENCY_RED_LINE")

    def test_symptom_triage_dentist(self):
        res = assess_symptoms_and_recommend_specialty("Dor de dente e gengiva inchada")
        self.assertEqual(res["recommended_specialty"], "Dentista")
        self.assertFalse(res["is_emergency"])

    def test_availability_check_valid_date(self):
        res = check_medical_specialty_availability("Dentista", "2026-06-15")
        self.assertEqual(res["status"], "success")
        self.assertTrue(len(res["available_slots"]) > 0)

    def test_availability_check_invalid_date_guided_error(self):
        res = check_medical_specialty_availability("Dentista", "15-06-2026")
        self.assertEqual(res["status"], "error")
        self.assertIn("error_recovery_hint", res)
        self.assertIn("AAAA-MM-DD", res["error_recovery_hint"])

    def test_booking_without_hitl_confirmation(self):
        is_approved, error = HumanInTheLoopHook.verify_booking_confirmation(
            patient_id="Carlos Silva",
            slot_id="dentista_slot_1",
            confirmed_by_patient=False
        )
        self.assertFalse(is_approved)
        self.assertEqual(error["status"], "AWAITING_HUMAN_CONFIRMATION")

    def test_booking_with_hitl_confirmation(self):
        res = book_medical_appointment(
            patient_id="Carlos Silva",
            slot_id="dentista_slot_1",
            specialty="Dentista",
            date="2026-06-15",
            confirmed_by_patient=True
        )
        self.assertEqual(res["status"], "confirmed")
        self.assertIn("appointment_id", res)

    def test_pii_redaction(self):
        text_with_cpf = "O paciente com CPF 123.456.789-00 e email teste@email.com solicitou agendamento."
        redacted = PIIScrubber.redact(text_with_cpf)
        self.assertNotIn("123.456.789-00", redacted)
        self.assertIn("[REDACTED_CPF]", redacted)
        self.assertIn("[REDACTED_EMAIL]", redacted)

if __name__ == "__main__":
    unittest.main()
