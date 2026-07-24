#!/usr/bin/env python3
"""
Script simples para interagir localmente com o Symptom Navigator Agent no terminal.
"""
import os
import sys

# Define variáveis de ambiente padrão
os.environ.setdefault("GOOGLE_GENAI_USE_VERTEXAI", "true")
os.environ.setdefault("GOOGLE_CLOUD_LOCATION", "us-central1")

# Adiciona o diretório atual ao PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from google.adk.cli import main

if __name__ == "__main__":
    # Inicia o CLI interativo oficial do ADK apontando para a pasta symptom_navigator
    sys.argv = ["adk", "run", "symptom_navigator"]
    main()
