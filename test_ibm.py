import requests

API_KEY = "3ZyGd0q5Z571DeRDXb5ZmQOAjt2b5LbF9nPET_AEjQKs"
DEPLOYMENT_URL = "https://us-south.ml.cloud.ibm.com/ml/v4/deployments/4a3682fc-6bb8-42dc-8c35-a10b4a039a0c/ai_service?version=2021-05-01"

# 1. Generar token
token_response = requests.post(
    'https://iam.cloud.ibm.com/identity/token',
    data={
        "apikey": API_KEY,
        "grant_type": "urn:ibm:params:oauth:grant-type:apikey"
    },
    headers={"Content-Type": "application/x-www-form-urlencoded"}
)

if token_response.status_code != 200:
    print("Error al generar token:", token_response.text)
    exit()

mltoken = token_response.json()["access_token"]
print("Token generado correctamente ✅")

# 2. Cabecera para enviar al deployment
headers = {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer ' + mltoken
}

# 3. Función de chat interactivo
def chat_with_granite():
    print("\nEscribe 'salir' para terminar el chat.\n")
    while True:
        user_input = input("Tú: ")
        if user_input.lower() == "salir":
            break

        # Payload mínimo compatible
        payload = {
            "messages": [
                {"role": "user", "content": user_input}
            ]
        }

        try:
            response = requests.post(DEPLOYMENT_URL, json=payload, headers=headers)
            data = response.json()
            # Dependiendo del deployment, la respuesta puede estar en distintas rutas
            print("Granite:", data)
        except Exception as e:
            print("Error al llamar al modelo:", e)

# 4. Iniciar chat
chat_with_granite()