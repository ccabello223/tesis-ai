import os
from dotenv import load_dotenv
from google import genai
from google.genai import types
import pathlib
import sqlite3
from typing import List, Dict, Optional
from datetime import datetime


load_dotenv()
API_KEY = os.getenv("GOOGLE_GENAI_API_KEY")

if not API_KEY:
    raise ValueError("No se encontró la variable de entorno 'GOOGLE_GENAI_API_KEY'")

# aqui esta la base de datos para probar ojo despues vemos como se hace para unir la funcion de bd con la de gemini
def setup_database():
    conn = sqlite3.connect('tesisIA.db')
    cursor = conn.cursor()

    # Tabla User
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS User (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        correo TEXT NOT NULL,
        password TEXT NOT NULL,
        nombre TEXT NOT NULL,
        usuario TEXT NOT NULL
    )
    ''')

    # Tabla Chat
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Chat (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        titulo TEXT ,
        FOREIGN KEY (user_id) REFERENCES User(id)
    )
    ''')

    # Tabla Historial
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Historial (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        chat_id INTEGER NOT NULL,
        orden INTEGER NOT NULL,
        role TEXT NOT NULL,
        contenido TEXT NOT NULL,
        fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (chat_id) REFERENCES Chat(id)
    )
    ''')

    # Verificar si hay usuarios existentes
    cursor.execute("SELECT COUNT(*) FROM User")
    if cursor.fetchone()[0] == 0:
        users = [
            ('juan@example.com', 'pass123', 'Juan Pérez', 'juanp'),
            ('maria@example.com', '123456', 'María López', 'marial'),
            ('carlos@example.com', 'abc123', 'Carlos Gómez', 'carlosg'),
        ]
        cursor.executemany('''
        INSERT INTO User (correo, password, nombre, usuario) 
        VALUES (?, ?, ?, ?)
        ''', users)

    conn.commit()
    conn.close()
    print("Base de datos inicializada correctamente.")




class Gemini:
    def __init__(self):
        self.client = genai.Client(api_key=API_KEY)
        self.current_chat_id = None
        self.db_connection = sqlite3.connect('tesisIA.db')
        
    def __del__(self):
        self.db_connection.close()
    
    def _crear_nuevo_chat(self, user_id: int, titulo: str = "Nuevo chat") -> int:
        """Crea un nuevo chat en la base de datos"""
        cursor = self.db_connection.cursor()
        cursor.execute(
            "INSERT INTO Chat (user_id, titulo) VALUES (?, ?)",
            (user_id, titulo)
        )
        self.db_connection.commit()
        return cursor.lastrowid
    
    def _guardar_mensaje(self, chat_id: int, role: str, contenido: str) -> int:
        """Guarda un mensaje en el historial"""
        cursor = self.db_connection.cursor()
        
        # Obtener el siguiente orden
        cursor.execute(
            "SELECT COALESCE(MAX(orden), 0) + 1 FROM Historial WHERE chat_id = ?",
            (chat_id,)
        )
        orden = cursor.fetchone()[0]
        
        cursor.execute(
            "INSERT INTO Historial (chat_id, orden, role, contenido) VALUES (?, ?, ?, ?)",
            (chat_id, orden, role, contenido)
        )
        self.db_connection.commit()
        return cursor.lastrowid
    
    def _cargar_historial(self, chat_id: int) -> List[Dict[str, str]]:
        """Carga el historial de un chat desde la base de datos"""
        cursor = self.db_connection.cursor()
        cursor.execute(
            "SELECT role, contenido FROM Historial WHERE chat_id = ? ORDER BY orden",
            (chat_id,)
        )
        return [{"role": row[0], "content": row[1]} for row in cursor.fetchall()]
    
    def generar_respuesta(self, prompt: str, chat_id: Optional[int] = None, user_id: Optional[int] = None) -> str:
        """
        Genera una respuesta manteniendo el contexto de la conversación.
        
        Args:
            prompt (str): El mensaje del usuario.
            chat_id (int): ID del chat existente. Si es None, se crea uno nuevo.
            user_id (int): ID del usuario (requerido si chat_id es None).
            
        Returns:
            str: La respuesta generada por el modelo.
        """
        if chat_id is None:
            if user_id is None:
                raise ValueError("Se requiere user_id para crear un nuevo chat")
            chat_id = self._crear_nuevo_chat(user_id)
            self.current_chat_id = chat_id
        
        # Guardar mensaje del usuario
        self._guardar_mensaje(chat_id, "user", prompt)
        
        # Cargar historial
        historial = self._cargar_historial(chat_id)
        
        # Crear contenido para el modelo
        contents = [types.Content(role=msg["role"], parts=[types.Part(text=msg["content"])]) 
                   for msg in historial]
        
        # Obtener respuesta
        response = self.client.models.generate_content(
            model="gemini-2.0-flash",
            contents=contents
        )
        
        # Guardar respuesta del modelo
        self._guardar_mensaje(chat_id, "model", response.text)
        
        return response.text
    
    def evaluar_pdf(self, pdf_path: pathlib.Path, prompt: str, chat_id: Optional[int] = None, 
                   user_id: Optional[int] = None) -> str:
        """
        Evalúa un PDF manteniendo el contexto de la conversación.
        """
        if not pdf_path.exists():
            raise FileNotFoundError(f"No se encontró el archivo: {pdf_path}")
            
        if chat_id is None:
            if user_id is None:
                raise ValueError("Se requiere user_id para crear un nuevo chat")
            chat_id = self._crear_nuevo_chat(user_id)
            self.current_chat_id = chat_id
        
        # Guardar mensaje del usuario
        self._guardar_mensaje(chat_id, "user", prompt)
        
        # Cargar historial (excluyendo el último mensaje)
        historial = self._cargar_historial(chat_id)[:-1]
        
        # Crear contenido
        contents = [types.Content(role=msg["role"], parts=[types.Part(text=msg["content"])]) 
                   for msg in historial]
        
        # Agregar PDF
        contents.append(types.Blob(
            mime_type='application/pdf',
            data=pdf_path.read_bytes()
        ))
        contents.append(types.Content(role="user", parts=[types.Part(text=prompt)]))
        
        # Obtener respuesta
        response = self.client.models.generate_content(
            model="gemini-2.0-flash",
            contents=contents
        )
        
        # Guardar respuesta del modelo
        self._guardar_mensaje(chat_id, "model", response.text)
        
        return response.text
    
    def obtener_chats_usuario(self, user_id: int) -> List[Dict]:
        """Obtiene todos los chats de un usuario"""
        cursor = self.db_connection.cursor()
        cursor.execute(
            "SELECT id, titulo, fecha_creacion FROM Chat WHERE user_id = ? ORDER BY fecha_creacion DESC",
            (user_id,)
        )
        return [{"id": row[0], "titulo": row[1], "fecha_creacion": row[2]} 
                for row in cursor.fetchall()]
    
    def obtener_historial_chat(self, chat_id: int) -> List[Dict]:
        """Obtiene el historial completo de un chat ordenado"""
        cursor = self.db_connection.cursor()
        cursor.execute(
            "SELECT role, contenido, fecha FROM Historial WHERE chat_id = ? ORDER BY orden",
            (chat_id,)
        )
        return [{"role": row[0], "content": row[1], "fecha": row[2]} 
                for row in cursor.fetchall()]
    
    def limpiar_historial(self, chat_id: int):
        """Elimina el historial de un chat"""
        cursor = self.db_connection.cursor()
        cursor.execute("DELETE FROM Historial WHERE chat_id = ?", (chat_id,))
        cursor.execute("DELETE FROM Chat WHERE id = ?", (chat_id,))
        self.db_connection.commit()





def main():
    # Configurar base de datos
    setup_database()
    
    # Crear instancia de Gemini
    gemini = Gemini()
    
    # ID de usuario de prueba (deberías obtenerlo de tu sistema de autenticación)
    user_id = 1  # Suponiendo que es Juan Pérez
    
    # Ejemplo 1: Nuevo chat
    print("\n--- Nuevo chat ---")
    pregunta = input("Escribe tu pregunta: ")
    respuesta1 = gemini.generar_respuesta(pregunta, user_id=user_id)
    print(f"Respuesta: {respuesta1}")
    
    # Continuar el mismo chat (obtener el ID del chat actual)
    chat_id = gemini.current_chat_id
    # respuesta2 = gemini.generar_respuesta("¿Cuál es la capital de Francia?", chat_id=chat_id)
    # print(f"Respuesta: {respuesta2}")
    
    # Ejemplo 2: Obtener todos los chats del usuario
    print("\n--- Chats del usuario ---")
    chats = gemini.obtener_chats_usuario(user_id)
    for chat in chats:
        print(f"Chat {chat['id']}: {chat['titulo']} ({chat['fecha_creacion']})")
    
    # Ejemplo 3: Obtener historial de un chat
    if chats:
        print("\n--- Historial del chat ---")
        historial = gemini.obtener_historial_chat(chat_id)
        for msg in historial:
            print(f"{msg['role']} ({msg['fecha']}): {msg['content']}")
    
    # Ejemplo con PDF (descomentar cuando tengas un archivo real)
    # pdf_path = pathlib.Path("ruta/al/archivo.pdf")
    # if pdf_path.exists():
    #     respuesta_pdf = gemini.evaluar_pdf(pdf_path, "Resume este documento", chat_id=chat_id)
    #     print(f"\nRespuesta PDF: {respuesta_pdf}")

if __name__ == "__main__":
    main()