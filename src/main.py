import flet as ft
from Frontend.Views.Register import Register
from Frontend.Views.Login import Login
from Frontend.Views.Chat import Chat

def main(page: ft.Page):
    page.clean()
    Chat(page)
    #Register(page)
    page.update()

ft.app(main)
