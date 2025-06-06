import flet as ft
from Frontend.Views.InitialView import InitialView


def main(page: ft.Page):
    page.clean()
    InitialView(page)
    page.update()

ft.app(main)
