import flet as ft
from Backend.models.gemini import Gemini


def Chat(page: ft.Page):
    page.title = "Chat Interface"
    page.window.min_width = 1000
    page.window.min_height = 800

    gemini_client = Gemini()
    current_user_id = 1

    # --- Sidebar (Left) ---
    sidebar = ft.Container(
        content=ft.Column(
            [
                ft.IconButton(
                    icon=ft.Icons.MENU,
                    icon_color=ft.Colors.WHITE,
                    icon_size=30,
                ),
                ft.Container(height=20),
                ft.IconButton(
                    icon=ft.Icons.ADD,
                    icon_color=ft.Colors.WHITE,
                    icon_size=30,
                    on_click=lambda e: new_chat(),
                ),
                ft.Container(expand=True),
                ft.IconButton(
                    icon=ft.Icons.HELP_OUTLINE,
                    icon_color=ft.Colors.WHITE,
                    icon_size=30,
                ),
                ft.IconButton(
                    icon=ft.Icons.SETTINGS,
                    icon_color=ft.Colors.WHITE,
                    icon_size=30,
                ),
            ],
            alignment=ft.MainAxisAlignment.START,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=0,
            expand=True,
        ),
        width=70,
        bgcolor="#1e2126",
    )

    # --- Chat State ---
    messages = []
    current_chat_id = None

    def update_chat():
        chat_column.controls.clear()
        if not messages:
            # Show welcome message if no messages yet
            chat_column.controls.append(
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Text(
                                "Hola",
                                size=60,
                                weight=ft.FontWeight.BOLD,
                                color=ft.Colors.BLUE_ACCENT_400,
                            ),
                            ft.Text(
                                "¿Cómo puedo ayudarte?",
                                size=20,
                                color=ft.Colors.WHITE,
                            ),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        alignment=ft.MainAxisAlignment.CENTER,
                    ),
                    expand=True,
                    alignment=ft.alignment.center,
                )
            )
        else:
            for msg_content, msg_role in messages:
                is_user = msg_role == "user"
                chat_column.controls.append(
                    ft.Row(
                        [
                            ft.Container(
                                content=ft.Text(
                                    msg_content,
                                    color=ft.Colors.WHITE,
                                    size=18,
                                    selectable=True,
                                ),
                                padding=ft.padding.symmetric(
                                    vertical=10, horizontal=18
                                ),
                                bgcolor="#1e2128" if is_user else "#1e1e1e",
                                border_radius=18,
                                width=min(600, max(80, len(msg_content) * 10)),
                                margin=ft.margin.only(top=4, bottom=4),
                                shadow=(
                                    ft.BoxShadow(
                                        spread_radius=0,
                                        blur_radius=0,
                                        color=ft.Colors.with_opacity(
                                            0.40, ft.Colors.BLACK
                                        ),
                                        offset=ft.Offset(0, 4),
                                    )
                                    if is_user
                                    else None
                                ),
                            )
                        ],
                        alignment=(
                            ft.MainAxisAlignment.END
                            if is_user
                            else ft.MainAxisAlignment.START
                        ),
                    )
                )
        chat_column.auto_scroll = True
        page.update()

    # --- Chat Messages Area (dynamic) ---
    chat_column = ft.Column(
        expand=True,
        width=page.width * 0.7,
        scroll=ft.ScrollMode.AUTO,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
    )

    def load_chat_history(chat_id_to_load: int):
        nonlocal messages, current_chat_id
        messages.clear()
        historial = gemini_client.obtener_historial_chat(chat_id_to_load)
        for msg in historial:
            messages.append((msg["content"], msg["role"]))
        current_chat_id = chat_id_to_load
        update_chat()

    def new_chat():
        nonlocal messages, current_chat_id
        messages.clear()
        current_chat_id = None
        update_chat()
        # Aquí podrías querer actualizar la lista de chats en la sidebar

    def send_message(e):
        nonlocal current_chat_id
        user_msg = input_field.value.strip()
        if user_msg:
            messages.append((user_msg, "user"))
            input_field.value = ""
            update_chat()

            # Llama a la API de Gemini
            try:
                response_text = gemini_client.generar_respuesta(
                    prompt=user_msg, chat_id=current_chat_id, user_id=current_user_id
                )
                # Actualiza el chat_id si se creó un nuevo chat
                if current_chat_id is None:
                    current_chat_id = gemini_client.current_chat_id

                messages.append((response_text, "model"))
            except Exception as ex:
                messages.append((f"Error al obtener respuesta: {ex}", "model"))
            finally:
                update_chat()

    # --- Input Bar ---
    input_field = ft.TextField(
        hint_text="Pregúntale a...",
        hint_style=ft.TextStyle(color=ft.Colors.GREY_600),
        border_radius=10,
        border_color=ft.Colors.BLUE_ACCENT_700,
        focused_border_color=ft.Colors.BLUE_ACCENT_400,
        filled=True,
        fill_color=ft.Colors.BLUE_GREY_900,
        text_style=ft.TextStyle(color=ft.Colors.WHITE),
        expand=True,
        content_padding=ft.padding.symmetric(vertical=10, horizontal=15),
        multiline=True,
        min_lines=1,
        max_lines=3,
    )

    input_bar = ft.Container(
        content=ft.Row(
            [
                ft.IconButton(
                    icon=ft.Icons.ATTACH_FILE,
                    icon_color=ft.Colors.WHITE,
                    icon_size=25,
                ),
                input_field,
                ft.IconButton(
                    icon=ft.Icons.SEND,
                    icon_color=ft.Colors.WHITE,
                    icon_size=25,
                    bgcolor=ft.Colors.BLUE_ACCENT_700,
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
                    on_click=send_message,
                ),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=10,
        ),
        padding=ft.padding.only(left=15, right=15, top=15, bottom=30),
        height=90,
        width=page.width * 0.6,
        alignment=ft.alignment.center,
        bgcolor="#1e2128",
        border_radius=15,
        shadow=ft.BoxShadow(
            spread_radius=0,
            blur_radius=0,
            color=ft.Colors.with_opacity(0.40, ft.Colors.BLACK),
            offset=ft.Offset(0, 4),
        ),
    )

    # --- Main Chat Area (Right) ---
    chat_area = ft.Container(
        content=ft.Column(
            [
                # Top Bar (Profile Icon)
                ft.Container(
                    content=ft.Row(
                        [
                            ft.Container(expand=True),
                            ft.IconButton(
                                icon=ft.Icons.PERSON,
                                icon_color=ft.Colors.WHITE,
                                icon_size=30,
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.END,
                        expand=True,
                    ),
                    height=50,
                    padding=ft.padding.only(right=15, top=10),
                ),
                ft.Container(
                    content=chat_column,
                    alignment=ft.alignment.center,
                    expand=True,
                ),
                ft.Row(
                    [ft.Column([input_bar, ft.Container()])],
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
            ]
        ),
        expand=True,
        bgcolor="#1e1e1e",
    )

    # Cargar historial del último chat o iniciar uno nuevo
    initial_chats = gemini_client.obtener_chats_usuario(current_user_id)
    if initial_chats:
        load_chat_history(initial_chats[0]["id"])
    else:
        update_chat()

    page.add(
        ft.Container(
            content=ft.Row(spacing=0, controls=[sidebar, chat_area]),
            expand=True,
        )
    )


if __name__ == "__main__":
    ft.app(target=Chat)
