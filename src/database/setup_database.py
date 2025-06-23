import sqlite3

def setup_database(conn: sqlite3.Connection):
    """
    Configura la base de datos si no existe, creando las tablas necesarias.
    Acepta una conexión SQLite existente como argumento.
    """
    cursor = conn.cursor()

    # Tabla de Usuarios
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS User (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        correo TEXT NOT NULL UNIQUE, -- Añadido UNIQUE para evitar correos duplicados
        password TEXT NOT NULL,
        nombre TEXT NOT NULL,
        usuario TEXT NOT NULL UNIQUE -- Añadido UNIQUE para evitar usuarios duplicados
    )
    ''')
    
    # Tabla de Chats
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Chat (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        titulo TEXT ,
        FOREIGN KEY (user_id) REFERENCES User(id)
    )
    ''')

    # Tabla de Historial
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

    # Datos de prueba
    users = [
        ('juan@example.com', 'pass123', 'Juan Pérez', 'juanp'),
        ('maria@example.com', '123456', 'María López', 'marial'),
        ('carlos@example.com', 'abc123', 'Carlos Gómez', 'carlosg'),
    ]

    # Insertar usuarios de prueba solo si no existen
    for correo, password, nombre, usuario in users:
        cursor.execute("SELECT id FROM User WHERE correo = ? OR usuario = ?", (correo, usuario))
        if cursor.fetchone() is None:
            cursor.execute('''
            INSERT INTO User (correo, password, nombre, usuario) 
            VALUES (?, ?, ?, ?)
            ''', (correo, password, nombre, usuario))
            print(f"Usuario '{usuario}' insertado.")
        else:
            print(f"Usuario '{usuario}' o correo '{correo}' ya existe, omitiendo inserción.")

    conn.commit()
    print("Base de datos inicializada o verificada.")

# Solo para ejecutar el archivo independiente
if __name__ == "__main__":
    test_conn = sqlite3.connect('tesisIA.db')
    setup_database(test_conn)
    test_conn.close() 