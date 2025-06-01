import os
from dotenv import load_dotenv
from google import genai
from google.genai import types
import pathlib
import sqlite3
from typing import List, Dict, Optional
from datetime import datetime
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'database'))
from database.setup_database import setup_database


load_dotenv()
API_KEY = os.getenv("GOOGLE_GENAI_API_KEY")

if not API_KEY:
    raise ValueError("No se encontró la variable de entorno 'GOOGLE_GENAI_API_KEY'")


class Gemini:
    def __init__(self):
        """
        Inicializa el cliente de Gemini y el ID del chat actual.
        La conexión a la base de datos no se abre aquí para evitar problemas de hilos.
        """
        self.client = genai.Client(api_key=API_KEY)
        self.current_chat_id = None
        
    def _get_db_connection(self) -> sqlite3.Connection:
        """
        Retorna una nueva conexión a la base de datos SQLite.
        Asegura que la base de datos se configure si es la primera vez.
        """
        conn = sqlite3.connect('tesisIA.db')
        setup_database(conn) 
        return conn

    def _crear_nuevo_chat(self, user_id: int, titulo: str = "Nuevo chat") -> int:
        """
        Crea un nuevo chat en la base de datos para un usuario dado.
        
        Args:
            user_id (int): El ID del usuario.
            titulo (str): El título del nuevo chat (por defecto "Nuevo chat").
            
        Returns:
            int: El ID del chat recién creado.
        """
        conn = self._get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO Chat (user_id, titulo) VALUES (?, ?)",
                (user_id, titulo)
            )
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()
    
    def _guardar_mensaje(self, chat_id: int, role: str, contenido: str) -> int:
        """
        Guarda un mensaje (del usuario o del modelo) en el historial de un chat.
        
        Args:
            chat_id (int): El ID del chat al que pertenece el mensaje.
            role (str): El rol del remitente ("user" o "model").
            contenido (str): El texto del mensaje.
            
        Returns:
            int: El ID del mensaje guardado.
        """
        conn = self._get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "SELECT COALESCE(MAX(orden), 0) + 1 FROM Historial WHERE chat_id = ?",
                (chat_id,)
            )
            orden = cursor.fetchone()[0]
            
            cursor.execute(
                "INSERT INTO Historial (chat_id, orden, role, contenido) VALUES (?, ?, ?, ?)",
                (chat_id, orden, role, contenido)
            )
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close() 
    
    def _cargar_historial(self, chat_id: int) -> List[Dict[str, str]]:
        """
        Carga el historial de mensajes de un chat específico desde la base de datos.
        
        Args:
            chat_id (int): El ID del chat cuyo historial se desea cargar.
            
        Returns:
            List[Dict[str, str]]: Una lista de diccionarios, donde cada diccionario
                                   representa un mensaje con su "role" y "content".
        """
        conn = self._get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "SELECT role, contenido FROM Historial WHERE chat_id = ? ORDER BY orden",
                (chat_id,)
            )
            return [{"role": row[0], "content": row[1]} for row in cursor.fetchall()]
        finally:
            conn.close() 
    
    def generar_respuesta(self, prompt: str, chat_id: Optional[int] = None, user_id: Optional[int] = None) -> str:
        """
        Genera una respuesta del modelo Gemini, manteniendo el contexto de la conversación.
        Si no se proporciona un chat_id, se crea un nuevo chat.
        
        Args:
            prompt (str): El mensaje del usuario.
            chat_id (Optional[int]): ID del chat existente. Si es None, se crea uno nuevo.
            user_id (Optional[int]): ID del usuario (requerido si chat_id es None para crear un nuevo chat).
            
        Returns:
            str: La respuesta generada por el modelo.
        """
        if chat_id is None:
            if user_id is None:
                raise ValueError("Se requiere user_id para crear un nuevo chat si chat_id es None.")
            chat_id = self._crear_nuevo_chat(user_id)
            self.current_chat_id = chat_id 
        else:
            self.current_chat_id = chat_id 


        self._guardar_mensaje(chat_id, "user", prompt)
        

        historial = self._cargar_historial(chat_id)
        

        contents = [types.Content(role=msg["role"], parts=[types.Part(text=msg["content"])]) 
                    for msg in historial]
        

        response = self.client.models.generate_content(
            model="gemini-2.0-flash",
            contents=contents
        )
        
        self._guardar_mensaje(chat_id, "model", response.text)
        return response.text
    
    def evaluar_pdf(self, pdf_path: pathlib.Path, prompt: str, chat_id: Optional[int] = None, 
                     user_id: Optional[int] = None) -> str:
        """
        Evalúa un archivo PDF utilizando el modelo Gemini, manteniendo el contexto de la conversación.
        
        Args:
            pdf_path (pathlib.Path): La ruta al archivo PDF.
            prompt (str): El mensaje o pregunta del usuario sobre el PDF.
            chat_id (Optional[int]): ID del chat existente. Si es None, se crea uno nuevo.
            user_id (Optional[int]): ID del usuario (requerido si chat_id es None).
            
        Returns:
            str: La respuesta generada por el modelo basada en el PDF y el prompt.
        
        Raises:
            FileNotFoundError: Si el archivo PDF no se encuentra.
            ValueError: Si user_id no se proporciona para un nuevo chat.
        """
        if not pdf_path.exists():
            raise FileNotFoundError(f"No se encontró el archivo: {pdf_path}")
            
        if chat_id is None:
            if user_id is None:
                raise ValueError("Se requiere user_id para crear un nuevo chat si chat_id es None.")
            chat_id = self._crear_nuevo_chat(user_id)
            self.current_chat_id = chat_id
        else:
            self.current_chat_id = chat_id


        self._guardar_mensaje(chat_id, "user", prompt)
        

        historial = self._cargar_historial(chat_id)[:-1] 
        
        contents = [types.Content(role=msg["role"], parts=[types.Part(text=msg["content"])]) 
                    for msg in historial]
        

        contents.append(types.Blob(
            mime_type='application/pdf',
            data=pdf_path.read_bytes()
        ))
        contents.append(types.Content(role="user", parts=[types.Part(text=prompt)]))
        

        response = self.client.models.generate_content(
            model="gemini-2.0-flash",
            contents=contents
        )
        

        self._guardar_mensaje(chat_id, "model", response.text)
        
        return response.text
    
    def obtener_chats_usuario(self, user_id: int) -> List[Dict]:
        """
        Obtiene todos los chats asociados a un ID de usuario específico.
        
        Args:
            user_id (int): El ID del usuario.
            
        Returns:
            List[Dict]: Una lista de diccionarios, donde cada diccionario representa
                        un chat con su "id", "titulo" y "fecha_creacion".
        """
        conn = self._get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "SELECT id, titulo, fecha_creacion FROM Chat WHERE user_id = ? ORDER BY fecha_creacion DESC",
                (user_id,)
            )
            return [{"id": row[0], "titulo": row[1], "fecha_creacion": row[2]} 
                    for row in cursor.fetchall()]
        finally:
            conn.close() 
    
    def obtener_historial_chat(self, chat_id: int) -> List[Dict]:
        """
        Obtiene el historial completo de mensajes de un chat específico, ordenado cronológicamente.
        
        Args:
            chat_id (int): El ID del chat cuyo historial se desea obtener.
            
        Returns:
            List[Dict]: Una lista de diccionarios, donde cada diccionario representa
                        un mensaje con su "role", "content" y "fecha".
        """
        conn = self._get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "SELECT role, contenido, fecha FROM Historial WHERE chat_id = ? ORDER BY orden",
                (chat_id,)
            )
            return [{"role": row[0], "content": row[1], "fecha": row[2]} 
                    for row in cursor.fetchall()]
        finally:
            conn.close()
    
    def limpiar_historial(self, chat_id: int):
        """
        Elimina todos los mensajes del historial de un chat y el chat mismo.
        
        Args:
            chat_id (int): El ID del chat a limpiar y eliminar.
        """
        conn = self._get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM Historial WHERE chat_id = ?", (chat_id,))
            cursor.execute("DELETE FROM Chat WHERE id = ?", (chat_id,))
            conn.commit()
            print(f"Historial y chat {chat_id} limpiados y eliminados.")
        finally:
            conn.close() 


# Esto solo se ejecuta si el archivo gemini.py se corre directamente.
if __name__ == "__main__":
    print("Iniciando pruebas de la clase Gemini...")

    initial_conn = sqlite3.connect('tesisIA.db')
    setup_database(initial_conn)
    initial_conn.close() 
    print("Base de datos configurada.")

    # Crear una instancia de Gemini
    gemini_instance = Gemini()
    test_user_id = 1 

    # Ejemplo 1: Nuevo chat y primera pregunta
    print("\n--- Ejemplo: Nuevo chat y primera pregunta ---")
    pregunta_inicial = "Hola Gemini, ¿puedes decirme algo interesante sobre el espacio?"
    print(f"Usuario ({test_user_id}): {pregunta_inicial}")
    respuesta_inicial = gemini_instance.generar_respuesta(pregunta_inicial, user_id=test_user_id)
    print(f"Gemini: {respuesta_inicial}")
    current_test_chat_id = gemini_instance.current_chat_id
    print(f"ID del chat actual: {current_test_chat_id}")

    # Ejemplo 2: Continuar el mismo chat
    print("\n--- Ejemplo: Continuar el mismo chat ---")
    pregunta_seguimiento = "¿Y qué hay de los agujeros negros?"
    print(f"Usuario ({test_user_id}): {pregunta_seguimiento}")
    respuesta_seguimiento = gemini_instance.generar_respuesta(pregunta_seguimiento, chat_id=current_test_chat_id)
    print(f"Gemini: {respuesta_seguimiento}")

    # Ejemplo 3: Obtener todos los chats del usuario
    print("\n--- Ejemplo: Chats del usuario ---")
    chats_del_usuario = gemini_instance.obtener_chats_usuario(test_user_id)
    if chats_del_usuario:
        for chat in chats_del_usuario:
            print(f"Chat ID: {chat['id']}, Título: '{chat['titulo']}', Creado: {chat['fecha_creacion']}")
    else:
        print("No se encontraron chats para este usuario.")

    # Ejemplo 4: Obtener historial de un chat específico
    if current_test_chat_id:
        print(f"\n--- Ejemplo: Historial del chat {current_test_chat_id} ---")
        historial_completo = gemini_instance.obtener_historial_chat(current_test_chat_id)
        for msg in historial_completo:
            print(f"[{msg['fecha']}] {msg['role'].capitalize()}: {msg['content']}")


    print("\nPruebas de Gemini finalizadas.")