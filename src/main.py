import flet as ft
from Frontend.Views.Register import Register


def main(page: ft.Page):
    page.clean()
    Register(page)
    page.update()

ft.app(main)
