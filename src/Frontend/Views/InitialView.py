import flet as ft
from Frontend.Views.Register import Register
from Frontend.Views.Login import Login


def InitialView(page: ft.Page):
    page.title = "ANGLAI - Tu Amigo Colibrí"
    page.vertical_alignment = ft.CrossAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.bgcolor = ft.Colors.BLUE_700
    page.window_width = 800
    page.window_height = 700
    page.window_resizable = False

    text_animation = ft.Animation(600, ft.AnimationCurve.EASE_OUT_SINE)

    anglai_logo = ft.Image(
        src="src/assets/logo.png",
        width=150,
        height=150,
        opacity=0,
        animate_opacity=ft.Animation(500, ft.AnimationCurve.EASE_IN_OUT),
        animate_scale=ft.Animation(600, ft.AnimationCurve.EASE_OUT_BACK),
    )

    title = ft.Text(
        "ANGLAI",
        size=60,
        weight=ft.FontWeight.BOLD,
        color=ft.Colors.WHITE,
        opacity=0,
        animate_opacity=text_animation,
        animate_offset=text_animation,
    )

    subtitle = ft.Text(
        "Tu Amigo Colibrí",
        size=30,
        color=ft.Colors.CYAN_200,
        italic=True,
        opacity=0,
        animate_opacity=text_animation,
        animate_offset=text_animation,
    )

    description = ft.Text(
        "Te ayuda a hacer tu tesis de una manera rápida y sencilla.",
        size=20,
        color=ft.Colors.BLUE_GREY_100,
        text_align=ft.TextAlign.CENTER,
        opacity=0,
        animate_opacity=text_animation,
        animate_offset=text_animation,
    )

    def navigate_to_login(e):
        page.clean()
        Login(page)
        page.update()

    def navigate_to_signup(e):
        page.clean()
        Register(page)
        page.update()

    login_button = ft.ElevatedButton(
        text="Inicia Sesión",
        icon=ft.Icons.LOGIN,
        bgcolor=ft.Colors.CYAN_ACCENT_400,
        color=ft.Colors.BLUE_GREY_900,
        height=50,
        width=250,
        opacity=0,
        animate_opacity=ft.Animation(800, ft.AnimationCurve.EASE_IN),
        on_click=navigate_to_login,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)),
    )

    join_button = ft.OutlinedButton(
        text="Únete a la Aventura ANGLAI",
        icon=ft.Icons.PERSON_ADD,
        height=50,
        width=250,
        opacity=0,
        animate_opacity=ft.Animation(900, ft.AnimationCurve.EASE_IN),
        on_click=navigate_to_signup,
    )

    main_content = ft.Column(
        [
            anglai_logo,
            ft.Container(height=20),
            title,
            subtitle,
            ft.Container(height=30),
            description,
            ft.Container(height=50),
            login_button,
            ft.Container(height=15),
            join_button,
        ],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=0,
    )

    page.add(main_content)
    page.update()

    anglai_logo.opacity = 1
    page.update()
    import time

    time.sleep(0.3)

    title.opacity = 1
    page.update()
    time.sleep(0.2)

    subtitle.opacity = 1
    page.update()
    time.sleep(0.2)

    description.opacity = 1
    page.update()
    time.sleep(0.3)

    login_button.opacity = 1
    page.update()
    time.sleep(0.1)

    join_button.opacity = 1
    page.update()
