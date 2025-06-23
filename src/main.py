import os
import sqlite3
import flet as ft
from Frontend.Views.InitialView import InitialView
from database.setup_database import setup_database


def main(page: ft.Page):
    db_path = 'tesisIA.db'
    if not os.path.exists(db_path):
        print("La base de datos no existe. Creándola...")
        conn = sqlite3.connect(db_path)
        setup_database(conn)
        conn.close()
    else:
        print("BD ya creada.")

    page.clean()
    InitialView(page)
    page.update()

ft.app(main)