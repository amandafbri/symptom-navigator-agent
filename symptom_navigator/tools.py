def match_symptoms_to_specialty(symptoms: str) -> dict:
    """Mapeia os sintomas informados pelo paciente para a especialidade médica correta.

    Args:
        symptoms: Descrição dos sintomas fornecidos pelo paciente (ex: 'Estou com dor no peito').

    Returns:
        Um dicionário contendo a especialidade médica identificada.
    """
    symptoms_lower = symptoms.lower()
    
    # Mapeamentos simples de sintomas para especialidades
    if any(word in symptoms_lower for word in ["peito", "coração", "infarto", "pressão"]):
        specialty = "Cardiologista"
    elif any(word in symptoms_lower for word in ["osso", "fratura", "costas", "joelho", "torção", "coluna"]):
        specialty = "Ortopedista"
    elif any(word in symptoms_lower for word in ["dente", "boca", "gengiva"]):
        specialty = "Dentista"
    elif any(word in symptoms_lower for word in ["olho", "visão", "enxergar"]):
        specialty = "Oftalmologista"
    elif any(word in symptoms_lower for word in ["pele", "alergia", "coceira", "mancha"]):
        specialty = "Dermatologista"
    else:
        specialty = "Clínico Geral"

    return {
        "symptoms": symptoms,
        "specialty": specialty
    }


def check_availability(specialty: str, date: str) -> dict:
    """Busca os horários e vagas disponíveis na clínica para uma determinada especialidade e data.

    Args:
        specialty: A especialidade médica (ex: 'Cardiologista', 'Ortopedista', 'Clínico Geral').
        date: A data no formato 'AAAA-MM-DD' (ex: '2026-06-15').

    Returns:
        Um dicionário com a lista de horários/slots disponíveis.
    """
    # Retorna alguns horários mockados com base na especialidade
    slots = [
        {"slot_id": f"{specialty.lower()}_1", "time": "09:00", "doctor": "Dr. Silva"},
        {"slot_id": f"{specialty.lower()}_2", "time": "10:30", "doctor": "Dr. Oliveira"},
        {"slot_id": f"{specialty.lower()}_3", "time": "14:00", "doctor": "Dr. Santos"},
        {"slot_id": f"{specialty.lower()}_4", "time": "15:30", "doctor": "Dr. Souza"},
    ]
    
    return {
        "specialty": specialty,
        "date": date,
        "available_slots": slots
    }


def book_appointment(patient_id: str, slot_id: str) -> dict:
    """Efetiva o agendamento da consulta médica para o paciente no slot selecionado.

    Args:
        patient_id: O identificador único do paciente (pode ser o nome completo, CPF ou ID).
        slot_id: O identificador único do horário/slot de consulta selecionado (retornado pelo check_availability).

    Returns:
        Um dicionário com o status do agendamento e os detalhes da confirmação.
    """
    return {
        "status": "confirmed",
        "patient_id": patient_id,
        "slot_id": slot_id,
        "message": f"Consulta agendada com sucesso para o paciente '{patient_id}' no horário correspondente ao slot '{slot_id}'."
    }
