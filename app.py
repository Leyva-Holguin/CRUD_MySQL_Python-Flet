import flet as ft
import mysql.connector
import bcrypt
import re
import os
import shutil

def main(page: ft.Page):
    page.title = "Sistema de Gestión de Alumnos"
    page.bgcolor = ft.Colors.PURPLE_50
    page.theme_mode = ft.ThemeMode.LIGHT
    page.theme = ft.Theme(
        color_scheme=ft.ColorScheme(
            primary=ft.Colors.PURPLE,
            primary_container=ft.Colors.PURPLE_100,
            secondary=ft.Colors.PINK,
            secondary_container=ft.Colors.PINK_100,
        ),
    )

    current_user           = None
    selected_matricula     = None
    ruta_foto_seleccionada = ""
    CARPETA_FOTOS          = "fotos_perfil"
    SHADOW_COLOR           = "#1A000000"

    if not os.path.exists(CARPETA_FOTOS):
        os.makedirs(CARPETA_FOTOS)

    # ── Base de datos ────────────────────────────────────────────────────────
    try:
        conexion_db = mysql.connector.connect(
            host="localhost", user="root", password="admin123"
        )
        cursor_db = conexion_db.cursor()
        cursor_db.execute("CREATE DATABASE IF NOT EXISTS sistema_alumnos")
        cursor_db.execute("USE sistema_alumnos")
        cursor_db.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id INT PRIMARY KEY AUTO_INCREMENT,
                username VARCHAR(50) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL
            )
        """)
        cursor_db.execute("""
            CREATE TABLE IF NOT EXISTS alumnos (
                matricula VARCHAR(20) PRIMARY KEY,
                apellido_paterno VARCHAR(50) NOT NULL,
                apellido_materno VARCHAR(50) NOT NULL,
                nombre VARCHAR(50) NOT NULL,
                curp VARCHAR(18) UNIQUE NOT NULL,
                especialidad VARCHAR(100) NOT NULL,
                telefono VARCHAR(10) NOT NULL,
                ciudad_origen VARCHAR(100) NOT NULL,
                estado VARCHAR(50) NOT NULL,
                disciplina VARCHAR(100),
                foto_ruta VARCHAR(255)
            )
        """)
        cursor_db.execute("SELECT COUNT(*) FROM usuarios")
        if cursor_db.fetchone()[0] == 0:
            salt = bcrypt.gensalt()
            ph   = bcrypt.hashpw("admin123".encode(), salt)
            cursor_db.execute(
                "INSERT INTO usuarios (username, password_hash) VALUES (%s, %s)",
                ("admin", ph)
            )
        conexion_db.commit()
    except Exception as e:
        print(f"Error de conexión a MySQL: {e}")
        return

    # ── Helpers ──────────────────────────────────────────────────────────────
    def mostrar_mensaje(texto, color):
        snack = ft.SnackBar(
            content=ft.Text(texto, color=ft.Colors.WHITE),
            bgcolor=color, duration=3000, open=True
        )
        page.overlay.append(snack)
        page.update()

    def validar_curp(curp):
        return bool(re.match(r'^[A-Z]{4}\d{6}[A-Z]{6}\d{2}$', curp.upper()))

    def validar_telefono(tel):
        return bool(re.match(r'^\d{10}$', tel))

    # ════════════════════════════════════════════════════════════════════════
    #  LOGIN
    # ════════════════════════════════════════════════════════════════════════
    def ir_login():
        nonlocal current_user
        current_user = None

        txt_usuario  = ft.TextField(
            label="Usuario", width=320, prefix_icon=ft.Icons.PERSON,
            autofocus=True,
            border_color=ft.Colors.PURPLE_200,
            focused_border_color=ft.Colors.PURPLE
        )
        txt_password = ft.TextField(
            label="Contraseña", width=320, password=True,
            can_reveal_password=True, prefix_icon=ft.Icons.LOCK,
            border_color=ft.Colors.PURPLE_200,
            focused_border_color=ft.Colors.PURPLE
        )
        lbl_error = ft.Text("", color=ft.Colors.PINK_400, size=12)

        def iniciar_sesion(e):
            nonlocal current_user
            u = txt_usuario.value.strip()
            p = txt_password.value
            if not u or not p:
                lbl_error.value = "Complete todos los campos"
                page.update(); return
            try:
                cursor_db.execute(
                    "SELECT password_hash FROM usuarios WHERE username=%s", (u,)
                )
                row = cursor_db.fetchone()
                if row:
                    bh = row[0] if isinstance(row[0], bytes) else row[0].encode()
                    if bcrypt.checkpw(p.encode(), bh):
                        current_user = u
                        ir_panel()
                        return
                lbl_error.value = "Usuario o contraseña incorrectos"
                page.update()
            except Exception as ex:
                lbl_error.value = f"Error: {ex}"
                page.update()

        card = ft.Container(
            content=ft.Column([
                ft.Icon(ft.Icons.SCHOOL, size=70, color=ft.Colors.PURPLE),
                ft.Text("SISTEMA DE GESTIÓN", size=24,
                        weight=ft.FontWeight.BOLD, color=ft.Colors.PURPLE_700),
                ft.Text("DE ALUMNOS", size=20,
                        weight=ft.FontWeight.W_500, color=ft.Colors.PURPLE_400),
                ft.Divider(height=20, color=ft.Colors.PURPLE_100),
                txt_usuario, txt_password, lbl_error,
                ft.Button("INGRESAR", on_click=iniciar_sesion,
                          width=320, height=45,
                          bgcolor=ft.Colors.PURPLE, color=ft.Colors.WHITE),
                ft.TextButton("Crear cuenta nueva",
                              on_click=lambda _: ir_registro()),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=15),
            width=420, padding=40,
            bgcolor=ft.Colors.WHITE, border_radius=30,
            shadow=ft.BoxShadow(blur_radius=15, color=SHADOW_COLOR)
        )

        page.controls.clear()
        page.overlay.clear()
        page.window.width  = 480
        page.window.height = 640
        page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        page.vertical_alignment   = ft.MainAxisAlignment.CENTER
        page.scroll = None
        page.add(card)
        page.update()

    # ════════════════════════════════════════════════════════════════════════
    #  REGISTRO
    # ════════════════════════════════════════════════════════════════════════
    def ir_registro():
        txt_u   = ft.TextField(label="Nuevo Usuario", width=320,
                               prefix_icon=ft.Icons.PERSON, autofocus=True,
                               border_color=ft.Colors.PURPLE_200,
                               focused_border_color=ft.Colors.PURPLE)
        txt_p   = ft.TextField(label="Contraseña", width=320,
                               password=True, can_reveal_password=True,
                               prefix_icon=ft.Icons.LOCK,
                               border_color=ft.Colors.PURPLE_200,
                               focused_border_color=ft.Colors.PURPLE)
        txt_c   = ft.TextField(label="Confirmar Contraseña", width=320,
                               password=True, can_reveal_password=True,
                               prefix_icon=ft.Icons.LOCK,
                               border_color=ft.Colors.PURPLE_200,
                               focused_border_color=ft.Colors.PURPLE)
        lbl_err = ft.Text("", color=ft.Colors.PINK_400, size=12)

        def registrar(e):
            u, p, c = txt_u.value.strip(), txt_p.value, txt_c.value
            if not u or not p:
                lbl_err.value = "Complete todos los campos"; page.update(); return
            if p != c:
                lbl_err.value = "Las contraseñas no coinciden"; page.update(); return
            try:
                salt = bcrypt.gensalt()
                ph   = bcrypt.hashpw(p.encode(), salt)
                cursor_db.execute(
                    "INSERT INTO usuarios (username, password_hash) VALUES (%s,%s)",
                    (u, ph)
                )
                conexion_db.commit()
                mostrar_mensaje(f"Usuario '{u}' creado", ft.Colors.PURPLE)
                ir_login()
            except mysql.connector.IntegrityError:
                lbl_err.value = "El usuario ya existe"; page.update()

        card = ft.Container(
            content=ft.Column([
                ft.Icon(ft.Icons.SCHOOL, size=60, color=ft.Colors.PURPLE),
                ft.Text("CREAR NUEVA CUENTA", size=24,
                        weight=ft.FontWeight.BOLD, color=ft.Colors.PURPLE_700),
                ft.Divider(height=20, color=ft.Colors.PURPLE_100),
                txt_u, txt_p, txt_c, lbl_err,
                ft.Button("Registrar", on_click=registrar,
                          width=320, height=45,
                          bgcolor=ft.Colors.PURPLE, color=ft.Colors.WHITE),
                ft.TextButton("Volver al Login", on_click=lambda _: ir_login()),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=15),
            width=420, padding=40,
            bgcolor=ft.Colors.WHITE, border_radius=30,
            shadow=ft.BoxShadow(blur_radius=15, color=SHADOW_COLOR)
        )

        page.controls.clear()
        page.overlay.clear()
        page.window.width  = 480
        page.window.height = 680
        page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        page.vertical_alignment   = ft.MainAxisAlignment.CENTER
        page.scroll = None
        page.add(card)
        page.update()

    # ════════════════════════════════════════════════════════════════════════
    #  PANEL PRINCIPAL
    # ════════════════════════════════════════════════════════════════════════
    def ir_panel():
        nonlocal selected_matricula, ruta_foto_seleccionada
        selected_matricula     = None
        ruta_foto_seleccionada = ""

        filtro_letras  = ft.InputFilter(allow=True,
                                        regex_string=r"[a-zA-ZáéíóúÁÉÍÓÚñÑ ]",
                                        replacement_string="")
        filtro_numeros = ft.InputFilter(allow=True, regex_string=r"[0-9]",
                                        replacement_string="")

        txt_matricula        = ft.TextField(label="Matrícula *", width=220)
        txt_apellido_paterno = ft.TextField(label="Apellido Paterno *",
                                            input_filter=filtro_letras, width=220)
        txt_apellido_materno = ft.TextField(label="Apellido Materno *",
                                            input_filter=filtro_letras, width=220)
        txt_nombres          = ft.TextField(label="Nombre(s) *",
                                            input_filter=filtro_letras, width=220)
        txt_curp             = ft.TextField(label="CURP *", max_length=18, width=220)
        txt_especialidad     = ft.TextField(label="Especialidad *",
                                            input_filter=filtro_letras, width=220)
        txt_telefono         = ft.TextField(label="Teléfono *", max_length=10,
                                            input_filter=filtro_numeros, width=220)
        txt_ciudad           = ft.TextField(label="Ciudad de Origen *",
                                            input_filter=filtro_letras, width=220)
        txt_estado = ft.Dropdown(label="Estado *", width=220, options=[
            ft.DropdownOption("CHIHUAHUA"),
            ft.DropdownOption("NUEVO LEÓN"),
            ft.DropdownOption("JALISCO"),
            ft.DropdownOption("CIUDAD DE MÉXICO"),
            ft.DropdownOption("SONORA"),
            ft.DropdownOption("COAHUILA"),
        ])
        txt_disciplina = ft.Dropdown(label="Disciplina Deportiva", width=220, options=[
            ft.DropdownOption("FÚTBOL"),
            ft.DropdownOption("BÁSQUETBOL"),
            ft.DropdownOption("VÓLEIBOL"),
            ft.DropdownOption("ATLETISMO"),
            ft.DropdownOption("NINGUNA"),
        ])

        IMG_DEFECTO = "https://cdn-icons-png.flaticon.com/512/3135/3135715.png"
        img_perfil  = ft.Image(src=IMG_DEFECTO, width=110, height=110,
                               fit="cover", border_radius=55)
        lbl_resultado = ft.Text("", size=12, color=ft.Colors.PURPLE_400)

        contenedor_tabla = ft.Container(
            content=ft.Column(scroll="auto"),
            height=280,
            bgcolor=ft.Colors.WHITE,
            border_radius=15,
            padding=20,
            border=ft.Border.all(1, ft.Colors.PURPLE_100),
        )
        txt_buscador = ft.TextField(
            label="Buscar por matrícula o apellido",
            width=350, prefix_icon=ft.Icons.SEARCH
        )

        # ── FilePicker ───────────────────────────────────────────────────────
        def al_seleccionar_archivo(e):
            nonlocal ruta_foto_seleccionada
            if e.files:
                ext = os.path.splitext(e.files[0].path)[1].lower()
                if ext in ['.jpg', '.jpeg', '.png', '.bmp']:
                    ruta_foto_seleccionada = e.files[0].path
                    img_perfil.src = ruta_foto_seleccionada
                    img_perfil.update()
                    mostrar_mensaje("Foto seleccionada", ft.Colors.PURPLE)
                else:
                    mostrar_mensaje("Formato inválido (.png .jpg .jpeg)",
                                    ft.Colors.PINK_400)

        file_picker = ft.FilePicker()
        file_picker.on_result = al_seleccionar_archivo

        # ── Limpiar ──────────────────────────────────────────────────────────
        def limpiar(e=None):
            nonlocal selected_matricula, ruta_foto_seleccionada
            for tf in [txt_matricula, txt_apellido_paterno, txt_apellido_materno,
                       txt_nombres, txt_curp, txt_especialidad,
                       txt_telefono, txt_ciudad]:
                tf.value = ""
            txt_matricula.disabled  = False
            txt_estado.value        = None
            txt_disciplina.value    = None
            selected_matricula      = None
            ruta_foto_seleccionada  = ""
            img_perfil.src          = IMG_DEFECTO
            lbl_resultado.value     = ""
            txt_matricula.focus()
            page.update()

        # ── Cargar tabla ─────────────────────────────────────────────────────
        def cargar_alumnos(busqueda=""):
            contenedor_tabla.content.controls.clear()
            try:
                if busqueda:
                    cursor_db.execute("""
                        SELECT matricula, apellido_paterno, apellido_materno,
                               nombre, curp, telefono, especialidad,
                               estado, disciplina, foto_ruta, ciudad_origen
                        FROM alumnos
                        WHERE matricula LIKE %s OR apellido_paterno LIKE %s
                        ORDER BY matricula
                    """, (f"%{busqueda}%", f"%{busqueda}%"))
                else:
                    cursor_db.execute("""
                        SELECT matricula, apellido_paterno, apellido_materno,
                               nombre, curp, telefono, especialidad,
                               estado, disciplina, foto_ruta, ciudad_origen
                        FROM alumnos ORDER BY matricula
                    """)
                alumnos = cursor_db.fetchall()

                if not alumnos:
                    contenedor_tabla.content.controls.append(
                        ft.Container(
                            content=ft.Text("No hay alumnos registrados",
                                            color=ft.Colors.GREY_500, size=14),
                            alignment=ft.alignment.center, padding=40
                        )
                    )
                else:
                    # Encabezados
                    contenedor_tabla.content.controls.append(
                        ft.Container(
                            content=ft.Row([
                                ft.Text("Foto",       weight=ft.FontWeight.BOLD,
                                        size=13, color=ft.Colors.PURPLE_700, width=60),
                                ft.Text("Matrícula",  weight=ft.FontWeight.BOLD,
                                        size=13, color=ft.Colors.PURPLE_700, width=100),
                                ft.Text("A. Paterno", weight=ft.FontWeight.BOLD,
                                        size=13, color=ft.Colors.PURPLE_700, width=110),
                                ft.Text("A. Materno", weight=ft.FontWeight.BOLD,
                                        size=13, color=ft.Colors.PURPLE_700, width=110),
                                ft.Text("Nombre(s)",  weight=ft.FontWeight.BOLD,
                                        size=13, color=ft.Colors.PURPLE_700, width=130),
                                ft.Text("CURP",       weight=ft.FontWeight.BOLD,
                                        size=13, color=ft.Colors.PURPLE_700, width=150),
                                ft.Text("Teléfono",   weight=ft.FontWeight.BOLD,
                                        size=13, color=ft.Colors.PURPLE_700, width=90),
                                ft.Text("Acciones",   weight=ft.FontWeight.BOLD,
                                        size=13, color=ft.Colors.PURPLE_700, width=100),
                            ], spacing=10),
                            padding=10
                        )
                    )
                    contenedor_tabla.content.controls.append(
                        ft.Divider(color=ft.Colors.PURPLE_100, height=1)
                    )

                    for reg in alumnos:
                        def crear_fila(a):
                            def editar(e):
                                nonlocal selected_matricula, ruta_foto_seleccionada
                                selected_matricula         = a[0]
                                txt_matricula.value        = a[0]
                                txt_matricula.disabled     = True
                                txt_apellido_paterno.value = a[1]
                                txt_apellido_materno.value = a[2]
                                txt_nombres.value          = a[3]
                                txt_curp.value             = a[4]
                                txt_telefono.value         = a[5]
                                txt_especialidad.value     = a[6]
                                txt_estado.value           = a[7]
                                txt_disciplina.value       = a[8] if a[8] else "NINGUNA"
                                txt_ciudad.value           = a[10]
                                if a[9] and os.path.exists(a[9]):
                                    ruta_foto_seleccionada = a[9]
                                    img_perfil.src         = a[9]
                                else:
                                    ruta_foto_seleccionada = ""
                                    img_perfil.src         = IMG_DEFECTO
                                lbl_resultado.value = f"✏ Editando: {a[0]}"
                                page.update()

                            def eliminar(e):
                                dialogo = ft.AlertDialog(
                                    modal=True,
                                    title=ft.Text("Confirmar eliminación"),
                                    content=ft.Text(
                                        f"¿Eliminar permanentemente al alumno {a[0]}?"
                                    ),
                                    actions=[
                                        ft.TextButton("Cancelar",
                                            on_click=lambda _: cerrar()),
                                        ft.Button("Eliminar",
                                            on_click=lambda _: confirmar(),
                                            bgcolor=ft.Colors.PINK_400,
                                            color=ft.Colors.WHITE),
                                    ],
                                )
                                def cerrar():
                                    dialogo.open = False
                                    page.update()

                                def confirmar():
                                    try:
                                        cursor_db.execute(
                                            "SELECT foto_ruta FROM alumnos WHERE matricula=%s",
                                            (a[0],)
                                        )
                                        rf = cursor_db.fetchone()
                                        if rf and rf[0] and os.path.exists(rf[0]):
                                            try: os.remove(rf[0])
                                            except: pass
                                        cursor_db.execute(
                                            "DELETE FROM alumnos WHERE matricula=%s", (a[0],)
                                        )
                                        conexion_db.commit()
                                    except Exception as ex:
                                        print(f"Error al eliminar: {ex}")
                                    dialogo.open = False
                                    page.update()
                                    mostrar_mensaje("Registro eliminado",
                                                    ft.Colors.PINK_400)
                                    cargar_alumnos(txt_buscador.value)
                                    limpiar()

                                page.overlay.append(dialogo)
                                dialogo.open = True
                                page.update()

                            foto_src  = (a[9] if a[9] and os.path.exists(a[9])
                                         else IMG_DEFECTO)
                            mini_foto = ft.Image(src=foto_src, width=30, height=30,
                                                 fit="cover", border_radius=15)
                            return ft.Container(
                                content=ft.Row([
                                    ft.Container(content=mini_foto, width=60,
                                                 alignment=ft.alignment.center_left),
                                    ft.Text(str(a[0]), size=12, width=100),
                                    ft.Text(str(a[1]), size=12, width=110),
                                    ft.Text(str(a[2]), size=12, width=110),
                                    ft.Text(str(a[3]), size=12, width=130),
                                    ft.Text(str(a[4]), size=12, width=150),
                                    ft.Text(str(a[5]), size=12, width=90),
                                    ft.Row([
                                        ft.IconButton(icon=ft.Icons.EDIT,
                                                      icon_size=18,
                                                      icon_color=ft.Colors.PURPLE,
                                                      on_click=editar),
                                        ft.IconButton(icon=ft.Icons.DELETE,
                                                      icon_size=18,
                                                      icon_color=ft.Colors.PINK_400,
                                                      on_click=eliminar),
                                    ], spacing=0),
                                ], spacing=10),
                                padding=5,
                            )
                        contenedor_tabla.content.controls.append(crear_fila(reg))

            except Exception as ex:
                print(f"Error al cargar lista: {ex}")

            contenedor_tabla.update()
            page.update()

        # ── Guardar ──────────────────────────────────────────────────────────
        def guardar(e):
            nonlocal ruta_foto_seleccionada
            if not all([txt_matricula.value, txt_apellido_paterno.value,
                        txt_apellido_materno.value, txt_nombres.value,
                        txt_curp.value, txt_especialidad.value,
                        txt_telefono.value, txt_ciudad.value, txt_estado.value]):
                mostrar_mensaje("Complete todos los campos obligatorios (*)",
                                ft.Colors.PINK_400); return
            if not validar_curp(txt_curp.value):
                mostrar_mensaje("CURP inválida (18 caracteres)",
                                ft.Colors.PINK_400); return
            if not validar_telefono(txt_telefono.value):
                mostrar_mensaje("Teléfono debe tener 10 dígitos",
                                ft.Colors.PINK_400); return

            ruta_final = None
            if ruta_foto_seleccionada and os.path.exists(ruta_foto_seleccionada):
                ext  = os.path.splitext(ruta_foto_seleccionada)[1]
                dest = os.path.join(CARPETA_FOTOS,
                                    f"{txt_matricula.value.upper()}{ext}")
                shutil.copy(ruta_foto_seleccionada, dest)
                ruta_final = dest

            try:
                cursor_db.execute("""
                    INSERT INTO alumnos (matricula, apellido_paterno, apellido_materno,
                        nombre, curp, especialidad, telefono, ciudad_origen,
                        estado, disciplina, foto_ruta)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """, (
                    txt_matricula.value.upper(),
                    txt_apellido_paterno.value.upper(),
                    txt_apellido_materno.value.upper(),
                    txt_nombres.value.upper(),
                    txt_curp.value.upper(),
                    txt_especialidad.value.upper(),
                    txt_telefono.value,
                    txt_ciudad.value.upper(),
                    txt_estado.value,
                    txt_disciplina.value if txt_disciplina.value else None,
                    ruta_final
                ))
                conexion_db.commit()
                mostrar_mensaje("✔ Alumno registrado correctamente",
                                ft.Colors.PURPLE)
                limpiar()
                cargar_alumnos(txt_buscador.value)
            except Exception:
                mostrar_mensaje("Error: matrícula o CURP ya existen.",
                                ft.Colors.PINK_400)

        # ── Actualizar ───────────────────────────────────────────────────────
        def actualizar(e):
            nonlocal selected_matricula, ruta_foto_seleccionada
            if not selected_matricula:
                mostrar_mensaje("Selecciona un alumno de la tabla primero",
                                ft.Colors.PINK_400); return
            if not all([txt_apellido_paterno.value, txt_apellido_materno.value,
                        txt_nombres.value, txt_curp.value, txt_especialidad.value,
                        txt_telefono.value, txt_ciudad.value, txt_estado.value]):
                mostrar_mensaje("Complete todos los campos obligatorios (*)",
                                ft.Colors.PINK_400); return
            if not validar_curp(txt_curp.value):
                mostrar_mensaje("CURP inválida", ft.Colors.PINK_400); return
            if not validar_telefono(txt_telefono.value):
                mostrar_mensaje("Teléfono debe tener 10 dígitos",
                                ft.Colors.PINK_400); return

            ruta_final = ruta_foto_seleccionada
            if (ruta_foto_seleccionada and os.path.exists(ruta_foto_seleccionada)
                    and CARPETA_FOTOS not in ruta_foto_seleccionada):
                ext  = os.path.splitext(ruta_foto_seleccionada)[1]
                dest = os.path.join(CARPETA_FOTOS, f"{selected_matricula}{ext}")
                shutil.copy(ruta_foto_seleccionada, dest)
                ruta_final = dest

            try:
                cursor_db.execute("""
                    UPDATE alumnos SET
                        apellido_paterno=%s, apellido_materno=%s,
                        nombre=%s, curp=%s, especialidad=%s,
                        telefono=%s, ciudad_origen=%s, estado=%s,
                        disciplina=%s, foto_ruta=%s
                    WHERE matricula=%s
                """, (
                    txt_apellido_paterno.value.upper(),
                    txt_apellido_materno.value.upper(),
                    txt_nombres.value.upper(),
                    txt_curp.value.upper(),
                    txt_especialidad.value.upper(),
                    txt_telefono.value,
                    txt_ciudad.value.upper(),
                    txt_estado.value,
                    txt_disciplina.value if txt_disciplina.value else None,
                    ruta_final,
                    selected_matricula
                ))
                conexion_db.commit()
                mostrar_mensaje("✔ Alumno actualizado correctamente",
                                ft.Colors.PURPLE)
                limpiar()
                cargar_alumnos(txt_buscador.value)
            except Exception as ex:
                mostrar_mensaje(f"Error al actualizar: {ex}", ft.Colors.PINK_400)

        def salir(e):
            try:
                cursor_db.close()
                conexion_db.close()
            except: pass
            page.window.close()

        txt_buscador.on_change = lambda _: cargar_alumnos(txt_buscador.value)

        # ── Layout ───────────────────────────────────────────────────────────
        header = ft.Container(
            content=ft.Row([
                ft.Row([
                    ft.Icon(ft.Icons.SCHOOL, color=ft.Colors.WHITE),
                    ft.Text("Sistema de Gestión de Alumnos", size=20,
                            weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                ]),
                ft.Row([
                    ft.Text(f"Usuario: {current_user}", size=13,
                            color=ft.Colors.PURPLE_100),
                    ft.IconButton(icon=ft.Icons.LOGOUT,
                                  icon_color=ft.Colors.WHITE,
                                  tooltip="Cerrar sesión",
                                  on_click=lambda _: ir_login()),
                ])
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            padding=15, bgcolor=ft.Colors.PURPLE, border_radius=15
        )

        form_card = ft.Container(
            content=ft.Row([
                ft.Column([
                    ft.Text("DATOS DEL ALUMNO", size=16,
                            weight=ft.FontWeight.BOLD,
                            color=ft.Colors.PURPLE_700),
                    ft.Row([txt_matricula, txt_apellido_paterno,
                            txt_apellido_materno], spacing=15),
                    ft.Row([txt_nombres, txt_curp, txt_especialidad], spacing=15),
                    ft.Row([txt_telefono, txt_ciudad, txt_estado], spacing=15),
                    ft.Row([txt_disciplina], spacing=15),
                    ft.Divider(height=5, color=ft.Colors.TRANSPARENT),
                    ft.Row([
                        ft.Button("💾 Guardar",   on_click=guardar,
                                  bgcolor=ft.Colors.PURPLE,
                                  color=ft.Colors.WHITE, width=130),
                        ft.Button("✏ Actualizar", on_click=actualizar,
                                  bgcolor=ft.Colors.PURPLE_300,
                                  color=ft.Colors.WHITE, width=130),
                        ft.Button("🗑 Limpiar",   on_click=limpiar,
                                  bgcolor=ft.Colors.PURPLE_100,
                                  color=ft.Colors.PURPLE_700, width=130),
                        ft.Button("⏻ Salir",      on_click=salir,
                                  bgcolor=ft.Colors.PINK_400,
                                  color=ft.Colors.WHITE, width=130),
                    ], spacing=10),
                    lbl_resultado,
                ], spacing=12, expand=True),

                ft.VerticalDivider(width=20, color=ft.Colors.PURPLE_50),

                ft.Column([
                    ft.Text("FOTO PERFIL", size=14,
                            weight=ft.FontWeight.BOLD,
                            color=ft.Colors.PURPLE_700),
                    ft.Container(
                        content=img_perfil,
                        border=ft.Border.all(2, ft.Colors.PURPLE_200),
                        border_radius=60, padding=4
                    ),
                    ft.Button(
                        "Cargar Foto",
                        icon=ft.Icons.UPLOAD_FILE,
                        on_click=lambda _: file_picker.pick_files(
                            allow_multiple=False,
                            file_type="image"
                        ),
                        bgcolor=ft.Colors.PURPLE_50,
                        color=ft.Colors.PURPLE
                    ),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                   spacing=10, width=170),
            ]),
            padding=25, bgcolor=ft.Colors.WHITE, border_radius=20,
            shadow=ft.BoxShadow(blur_radius=10, color=SHADOW_COLOR)
        )

        buscador_row = ft.Container(
            content=ft.Row([txt_buscador],
                           alignment=ft.MainAxisAlignment.END),
            padding=5
        )

        panel = ft.Column([
            header,
            form_card,
            buscador_row,
            contenedor_tabla,
        ], spacing=15)

        # Agregar FilePicker al overlay ANTES de renderizar
        page.controls.clear()
        page.overlay.clear()
        page.overlay.append(file_picker)
        page.window.width  = 1350
        page.window.height = 850
        page.horizontal_alignment = ft.CrossAxisAlignment.START
        page.vertical_alignment   = ft.MainAxisAlignment.START
        page.scroll = "always"
        page.add(panel)
        page.update()

        cargar_alumnos()

    # ── Arranque ─────────────────────────────────────────────────────────────
    ir_login()


if __name__ == "__main__":
    ft.run(main)