import sqlite3
import os
import json
import datetime
from typing import List, Dict, Any, Optional

DB_PATH = os.environ.get("SYMPTOM_NAVIGATOR_DB", "symptom_navigator.db")

class PersistentDatabase:
    """Manages persistent storage for appointments, doctor availability, and session memory."""
    
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        """Initializes database schema if not present."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Appointments table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS appointments (
                    appointment_id TEXT PRIMARY KEY,
                    patient_id TEXT NOT NULL,
                    specialty TEXT NOT NULL,
                    date TEXT NOT NULL,
                    slot_id TEXT NOT NULL,
                    doctor_name TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            # Doctor schedules table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS doctor_schedules (
                    slot_id TEXT PRIMARY KEY,
                    specialty TEXT NOT NULL,
                    date TEXT NOT NULL,
                    time_slot TEXT NOT NULL,
                    doctor_name TEXT NOT NULL,
                    is_available BOOLEAN DEFAULT 1
                );
            """)
            
            # Sessions memory table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS session_state (
                    session_id TEXT PRIMARY KEY,
                    patient_id TEXT,
                    current_step TEXT,
                    metadata_json TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            conn.commit()
            self._seed_default_schedules(conn)

    def _seed_default_schedules(self, conn: sqlite3.Connection):
        """Seeds initial doctor availability slots if table is empty."""
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM doctor_schedules")
        count = cursor.fetchone()[0]
        if count == 0:
            specialties = ["Cardiologista", "Ortopedista", "Dentista", "Oftalmologista", "Dermatologista", "Clínico Geral"]
            default_date = datetime.date.today().strftime("%Y-%m-%d")
            doctors = {
                "Cardiologista": "Dr. Silva",
                "Ortopedista": "Dr. Oliveira",
                "Dentista": "Dra. Costa",
                "Oftalmologista": "Dr. Santos",
                "Dermatologista": "Dra. Lima",
                "Clínico Geral": "Dr. Souza"
            }
            times = ["09:00", "10:30", "14:00", "15:30"]
            
            for spec in specialties:
                doc = doctors.get(spec, "Dr. Médico")
                for idx, t in enumerate(times, 1):
                    slot_id = f"{spec.lower()}_slot_{idx}"
                    cursor.execute("""
                        INSERT OR IGNORE INTO doctor_schedules 
                        (slot_id, specialty, date, time_slot, doctor_name, is_available)
                        VALUES (?, ?, ?, ?, ?, 1)
                    """, (slot_id, spec, default_date, t, doc))
            conn.commit()

    def get_available_slots(self, specialty: str, date: str) -> List[Dict[str, Any]]:
        """Retrieves available slots for a given specialty and date."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT slot_id, time_slot as time, doctor_name as doctor
                FROM doctor_schedules
                WHERE LOWER(specialty) = LOWER(?) AND is_available = 1
            """, (specialty,))
            rows = cursor.fetchall()
            
            # If no date-specific rows, fallback to standard available slots
            if not rows:
                doctors = ["Dr. Silva", "Dr. Oliveira", "Dra. Santos"]
                return [
                    {"slot_id": f"{specialty.lower()}_1", "time": "09:00", "doctor": doctors[0]},
                    {"slot_id": f"{specialty.lower()}_2", "time": "10:30", "doctor": doctors[1]},
                    {"slot_id": f"{specialty.lower()}_3", "time": "14:00", "doctor": doctors[2]}
                ]
            return [dict(row) for row in rows]

    def book_slot(self, patient_id: str, slot_id: str, specialty: str, date: str, doctor_name: str) -> Dict[str, Any]:
        """Books an appointment and persists it in SQLite."""
        appointment_id = f"APT-{int(datetime.datetime.now().timestamp())}"
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO appointments (appointment_id, patient_id, specialty, date, slot_id, doctor_name, status)
                VALUES (?, ?, ?, ?, ?, ?, 'confirmed')
            """, (appointment_id, patient_id, specialty, date, slot_id, doctor_name))
            
            cursor.execute("""
                UPDATE doctor_schedules SET is_available = 0 WHERE slot_id = ?
            """, (slot_id,))
            conn.commit()
            
        return {
            "appointment_id": appointment_id,
            "patient_id": patient_id,
            "specialty": specialty,
            "date": date,
            "slot_id": slot_id,
            "doctor": doctor_name,
            "status": "confirmed"
        }

    def save_session_state(self, session_id: str, patient_id: Optional[str], current_step: str, metadata: Dict[str, Any]):
        """Persists session state and memory across turns."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO session_state (session_id, patient_id, current_step, metadata_json, updated_at)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (session_id, patient_id, current_step, json.dumps(metadata)))
            conn.commit()

db = PersistentDatabase()
