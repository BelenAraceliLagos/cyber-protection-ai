import requests

OLLAMA_URL = "http://localhost:11434/api/generate"

MODEL = "llama3"

def generate_text(prompt: str):

    try:

        response = requests.post(
            OLLAMA_URL,
            json={
                "model": MODEL,
                "prompt": prompt,
                "stream": False
            },
            timeout=120
        )

        data = response.json()

        return data.get("response")

    except Exception as e:

        print("OLLAMA ERROR:", e)

        return """
        Informe generado temporalmente.

        No fue posible conectar con Ollama.
        """