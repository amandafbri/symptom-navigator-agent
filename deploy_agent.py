import os
import vertexai
from vertexai.agent_engines import AdkApp
from symptom_navigator.agent import root_agent

# Configurações do projeto e região
project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "amandafurtado-tests")
location = "us-central1"

# Bucket de staging para o deploy
staging_bucket = os.getenv("GCS_STAGING_BUCKET", f"gs://{project_id}-adk-staging") 

print("="*60)
print(f"🚀 Iniciando deploy do Agente no Agent Runtime...")
print(f"   Projeto: {project_id}")
print(f"   Região:  {location}")
print(f"   Bucket:  {staging_bucket}")
print("="*60)

# Inicializa o cliente Vertex AI
client = vertexai.Client(project=project_id, location=location)

# Cria a aplicação ADK para deploy
app = AdkApp(
    agent=root_agent,
    enable_tracing=True
)

print("\n📦 Enviando código e criando o Agent Engine (Isso pode levar alguns minutos)...")

remote_agent = client.agent_engines.create(
    agent=app,
    config={
        "requirements": [
            "google-adk",
            "google-cloud-aiplatform[adk,agent_engines]",
            "pydantic",
            "cloudpickle",
            "opentelemetry-instrumentation-google-genai",
            "opentelemetry-instrumentation-sqlite3",
            "opentelemetry-exporter-gcp-logging",
            "opentelemetry-exporter-gcp-monitoring",
            "opentelemetry-exporter-otlp-proto-grpc",
            "opentelemetry-instrumentation-vertexai",
            "opentelemetry-instrumentation-httpx",
            "opentelemetry-instrumentation-grpc"
        ],
        "staging_bucket": staging_bucket,
        "extra_packages": ["symptom_navigator"],
        "display_name": "Symptom Navigator",
        "description": "Agente que ajuda na triagem de pacientes",
        "agent_framework": "google-adk",
    },
)

print("\n✅ DEPLOY FINALIZADO COM SUCESSO!")
print(f"🔗 ID de Recurso do Agente: {remote_agent}")
