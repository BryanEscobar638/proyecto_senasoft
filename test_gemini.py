from google.oauth2 import service_account
import google.auth.transport.requests
import requests
import json

# Cargar credenciales de la cuenta de servicio
SCOPES = ["https://www.googleapis.com/auth/cloud-platform"]
credentials = service_account.Credentials.from_service_account_file(
    "C:/Users/Sena/Desktop/proyecto_senasoft_ia/credenciales.json",
    scopes=SCOPES
)

# Generar token válido
auth_req = google.auth.transport.requests.Request()
credentials.refresh(auth_req)
ACCESS_TOKEN = credentials.token

# Llamada a Gemini
url = "https://generativelanguage.googleapis.com/v1beta2/models/text-bison-001:generateText"
headers = {
    "Authorization": f"Bearer {ACCESS_TOKEN}",
    "Content-Type": "application/json"
}
data = {
    "prompt": "Resume este dataset de ejemplo.",
    "max_output_tokens": 200
}

response = requests.post(url, headers=headers, json=data)
print(response.json())
