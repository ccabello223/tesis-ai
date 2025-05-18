import flet as ft
from Frontend.Views.Login import Login

def Register(page: ft.Page):

    page.bgcolor = ft.Colors.TRANSPARENT
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.fonts = {
        "Aleo Bold Italic": "https://raw.githubusercontent.com/google/fonts/master/ofl/aleo/Aleo-BoldItalic.ttf"
    }

    page.window.always_on_top = True
    page.decoration = ft.BoxDecoration(
        image=ft.DecorationImage(
            src="https://searchengineland.com/wp-content/seloads/2015/05/brain-future-tech-implant-ss-1920.jpg",
            fit=ft.ImageFit.COVER,
        )
    )

    logo = ft.Image(src="src/assets/logo.png", width=150, height=150)

    title = ft.Text("Regístrate", font_family="Aleo Bold Italic", size=25)

    username = ft.TextField(
        multiline=False,
        label="Nombre de usuario",
        border_color=ft.Colors.BLUE_ACCENT_700,
    )
    email = ft.TextField(
        multiline=False,
        label="Correo electrónico",
        border_color=ft.Colors.BLUE_ACCENT_700,
        keyboard_type=ft.KeyboardType.EMAIL,
    )
    password = ft.TextField(
        multiline=False,
        label="Contraseña",
        password=True,
        border_color=ft.Colors.BLUE_ACCENT_700,
        can_reveal_password=True,
    )
    register_button = ft.ElevatedButton(
        text="Registrarse", 
        color="White", 
        bgcolor=ft.Colors.BLUE_ACCENT_700,
        width=200,
        on_click= lambda e: handle_register(page)
    )

    register_form = ft.Column(
        [logo, title, username, email, password, register_button],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        alignment=ft.MainAxisAlignment.CENTER,
        spacing=25,
    )

    register_contain = ft.Container(
        content=register_form,
        width=400,
        height=600,
        padding=40,
        alignment=ft.alignment.center,
        bgcolor=ft.Colors.BLACK,
        border_radius=20
    )

    page.add(register_contain)
    
    
        
    def handle_register(page: ft.Page):
        page.clean()
        Login(page)
        page.update()
        