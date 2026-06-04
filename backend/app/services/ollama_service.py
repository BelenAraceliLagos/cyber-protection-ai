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

        print("STATUS:", response.status_code)

        print("RAW RESPONSE:", response.text)

        data = response.json()

        generated_text = data.get("response")

        if not generated_text:

            return """
            ERROR:
            Ollama respondió vacío.
            """

        return generated_text

    except Exception as e:

        print("OLLAMA ERROR:", str(e))

        return f"""
        ERROR OLLAMA:
        {str(e)}
        """