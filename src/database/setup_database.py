import sqlite3

def setup_database():
    conn = sqlite3.connect('tesisIA.db')
    cursor = conn.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS User (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        correo TEXT NOT NULL,
        password TEXT NOT NULL,
        nombre TEXT NOT NULL,
        usuario TEXT NOT NULL
    )
    ''')

    #datos de test
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
    print("Base de datos inicializada con datos de prueba.")

if __name__ == "__main__":
    setup_database()