import os
from dotenv import load_dotenv

from google import genai
from google.genai import types
import pathlib

# Cargar variable de entorno
load_dotenv()

# Variable global para la API key
API_KEY = os.getenv("GOOGLE_GENAI_API_KEY")

if not API_KEY:
    raise ValueError("No se encontró la variable de entorno 'GOOGLE_GENAI_API_KEY'")

class Gemini:
    def __init__(self):
        self.client = genai.Client(api_key=API_KEY)

    def generar_respuesta(self, prompt: str) -> str:
        response = self.client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt
        )
        return response.text
    
    # Tienes que pasarle la ruta del archivo local y el prompt. Ejemplo de la ruta: src\assets\pdf\trabajo.pdf
    def evaluar_pdf(self, pdf_path: pathlib.Path, prompt: str) -> str:
        if not pdf_path.exists():
            raise FileNotFoundError(f"No se encontró el archivo: {pdf_path}")
        
        response = self.client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[
                types.from_bytes(
                    data=pdf_path.read_bytes(),
                    mime_type='application/pdf'
                ),
                prompt
            ]
        )
        return response.text