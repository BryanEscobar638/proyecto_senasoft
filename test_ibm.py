import requests

GEMINI_API_KEY = "AIzaSyDIthgBtbQ_q9ls8450_8l4AkFMAQgDL4g"
URL = "https://generativelanguage.googleapis.com/v1beta2/models/text-bison-001:generateText"

payload = {"prompt": "Hola, escribe un resumen breve de Python."}
headers = {"Authorization": f"Bearer {GEMINI_API_KEY}", "Content-Type": "application/json"}

response = requests.post(URL, json=payload, headers=headers)
print(response.status_code)
print(response.text)