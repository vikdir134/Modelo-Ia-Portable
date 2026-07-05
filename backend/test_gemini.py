from google import genai

client = genai.Client()

respuesta = client.models.generate_content(
    model="gemini-2.5-flash",
    contents="Responde solo: Gemini conectado correctamente."
)

print(respuesta.text)