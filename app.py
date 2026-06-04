import asyncio
import flet as ft
import mysql.connector
from mysql.connector import Error
import bcrypt
import re
import os
import shutil
import hashlib
from datetime import datetime


async def main(page: ft.Page):
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

    # Vista contenedora (nunca se elimina del arbol)
    vista_container = ft.Container(expand=True)
    page.add(vista_container)
    page.update()

    # Clase para manejo de conexion a Base de Datos
    class DatabaseManager:
        def __init__(self):
            self.connection = None
            self.config = {
                'host': 'localhost',
                'user': 'root',
                'password': 'admin123',
                'database': 'sistema_alumnos'
            }

        def connect(self):
            try:
                if self.connection is None or not self.connection.is_connected():
                    self.connection = mysql.connector.connect(**self.config)
                return self.connection
            except Error as e:
                print(f"Error de conexion: {e}")
                return None

        def execute_query(self, query, params=None):
            cursor = None
            try:
                conn = self.connect()
                if conn:
                    cursor = conn.cursor()
                    cursor.execute(query, params or ())
                    if query.strip().upper().startswith('SELECT'):
                        return cursor.fetchall()
                    else:
                        conn.commit()
                        return cursor.rowcount
            except Error as e:
                print(f"Error en consulta: {e}")
                if self.connection:
                    self.connection.rollback()
                raise e
            finally:
                if cursor:
                    cursor.close()
            return None

        def close(self):
            if self.connection and self.connection.is_connected():
                self.connection.close()
                self.connection = None

        def __enter__(self):
            self.connect()
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            self.close()

    # Inicializar base de datos
    try:
        temp_conn = mysql.connector.connect(
            host='localhost', user='root', password='admin123'
        )
        temp_cursor = temp_conn.cursor()
        temp_cursor.execute("CREATE DATABASE IF NOT EXISTS sistema_alumnos")
        temp_cursor.close()
        temp_conn.close()

        with DatabaseManager() as db_init:
            db_init.execute_query("""
                CREATE TABLE IF NOT EXISTS usuarios (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    username VARCHAR(50) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL
                )
            """)
            db_init.execute_query("""
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
            result = db_init.execute_query("SELECT COUNT(*) FROM usuarios")
            if result and result[0][0] == 0:
                salt = bcrypt.gensalt()
                ph = bcrypt.hashpw("admin123".encode(), salt)
                db_init.execute_query(
                    "INSERT INTO usuarios (username, password_hash) VALUES (%s, %s)",
                    ("admin", ph)
                )
    except Exception as e:
        print(f"Error inicializando BD: {e}")
        return

    # Helpers
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

    def manejar_foto(ruta_origen, matricula):
        if not ruta_origen or not os.path.exists(ruta_origen):
            return None
        ext = os.path.splitext(ruta_origen)[1].lower()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        with open(ruta_origen, 'rb') as f:
            file_hash = hashlib.md5(f.read()).hexdigest()[:8]
        nombre = f"{matricula}_{timestamp}_{file_hash}{ext}"
        destino = os.path.join(CARPETA_FOTOS, nombre)
        shutil.copy2(ruta_origen, destino)
        return destino

    # Navegacion
    def navegar(nuevo_control, ancho, alto, h_align, v_align, scroll):
        vista_container.content = nuevo_control
        vista_container.expand  = True
        page.window.width       = ancho
        page.window.height      = alto
        page.horizontal_alignment = h_align
        page.vertical_alignment   = v_align
        page.scroll = scroll
        page.update()

    # LOGIN
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
            label="Contrasena", width=320, password=True,
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
                temp_db = DatabaseManager()
                result = temp_db.execute_query(
                    "SELECT password_hash FROM usuarios WHERE username=%s", (u,)
                )
                temp_db.close()
                if result:
                    bh = result[0][0]
                    if not isinstance(bh, bytes):
                        bh = bh.encode()
                    if bcrypt.checkpw(p.encode(), bh):
                        current_user = u
                        ir_panel()
                        return
                lbl_error.value = "Usuario o contrasena incorrectos"
                page.update()
            except Exception as ex:
                lbl_error.value = f"Error: {ex}"
                page.update()

        card = ft.Container(
            content=ft.Column([
                ft.Icon(ft.Icons.SCHOOL, size=70, color=ft.Colors.PURPLE),
                ft.Text("SISTEMA DE GESTION", size=24,
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

        navegar(
            ft.Column([card], horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                      alignment=ft.MainAxisAlignment.CENTER, expand=True),
            480, 640,
            ft.CrossAxisAlignment.CENTER,
            ft.MainAxisAlignment.CENTER,
            None
        )

    # REGISTRO
    def ir_registro():
        txt_u = ft.TextField(label="Nuevo Usuario", width=320,
                             prefix_icon=ft.Icons.PERSON, autofocus=True,
                             border_color=ft.Colors.PURPLE_200,
                             focused_border_color=ft.Colors.PURPLE)
        txt_p = ft.TextField(label="Contrasena", width=320,
                             password=True, can_reveal_password=True,
                             prefix_icon=ft.Icons.LOCK,
                             border_color=ft.Colors.PURPLE_200,
                             focused_border_color=ft.Colors.PURPLE)
        txt_c = ft.TextField(label="Confirmar Contrasena", width=320,
                             password=True, can_reveal_password=True,
                             prefix_icon=ft.Icons.LOCK,
                             border_color=ft.Colors.PURPLE_200,
                             focused_border_color=ft.Colors.PURPLE)
        lbl_err = ft.Text("", color=ft.Colors.PINK_400, size=12)

        def registrar(e):
            u, p, c = txt_u.value.strip(), txt_p.value, txt_c.value
            if not u or not p:
                lbl_err.value = "Complete todos los campos"
                page.update(); return
            if p != c:
                lbl_err.value = "Las contrasenas no coinciden"
                page.update(); return
            try:
                salt = bcrypt.gensalt()
                ph   = bcrypt.hashpw(p.encode(), salt)
                temp_db = DatabaseManager()
                temp_db.execute_query(
                    "INSERT INTO usuarios (username, password_hash) VALUES (%s,%s)",
                    (u, ph)
                )
                temp_db.close()
                mostrar_mensaje(f"Usuario '{u}' creado", ft.Colors.PURPLE)
                ir_login()
            except mysql.connector.IntegrityError:
                lbl_err.value = "El usuario ya existe"; page.update()
            except Exception as ex:
                lbl_err.value = f"Error: {ex}"; page.update()

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

        navegar(
            ft.Column([card], horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                      alignment=ft.MainAxisAlignment.CENTER, expand=True),
            480, 680,
            ft.CrossAxisAlignment.CENTER,
            ft.MainAxisAlignment.CENTER,
            None
        )

    # PANEL PRINCIPAL
    def ir_panel():
        nonlocal selected_matricula, ruta_foto_seleccionada
        selected_matricula     = None
        ruta_foto_seleccionada = ""

        filtro_letras  = ft.InputFilter(allow=True,
                                        regex_string=r"[a-zA-ZáéíóúÁÉÍÓÚñÑ ]",
                                        replacement_string="")
        filtro_numeros = ft.InputFilter(allow=True, regex_string=r"[0-9]",
                                        replacement_string="")

        txt_matricula        = ft.TextField(label="Matricula *", width=220)
        txt_apellido_paterno = ft.TextField(label="Apellido Paterno *",
                                            input_filter=filtro_letras, width=220)
        txt_apellido_materno = ft.TextField(label="Apellido Materno *",
                                            input_filter=filtro_letras, width=220)
        txt_nombres          = ft.TextField(label="Nombre(s) *",
                                            input_filter=filtro_letras, width=220)
        txt_curp             = ft.TextField(label="CURP *", max_length=18, width=220)
        txt_especialidad     = ft.TextField(label="Especialidad *",
                                            input_filter=filtro_letras, width=220)
        txt_telefono         = ft.TextField(label="Telefono *", max_length=10,
                                            input_filter=filtro_numeros, width=220)
        txt_ciudad           = ft.TextField(label="Ciudad de Origen *",
                                            input_filter=filtro_letras, width=220)
        txt_estado = ft.Dropdown(label="Estado *", width=220, options=[
            ft.DropdownOption("CHIHUAHUA"),
            ft.DropdownOption("NUEVO LEON"),
            ft.DropdownOption("JALISCO"),
            ft.DropdownOption("CIUDAD DE MEXICO"),
            ft.DropdownOption("SONORA"),
            ft.DropdownOption("COAHUILA"),
        ])
        txt_disciplina = ft.Dropdown(label="Disciplina Deportiva", width=220, options=[
            ft.DropdownOption("FUTBOL"),
            ft.DropdownOption("BASQUETBOL"),
            ft.DropdownOption("VOLEIBOL"),
            ft.DropdownOption("ATLETISMO"),
            ft.DropdownOption("NINGUNA"),
        ])

        IMG_DEFECTO   = "https://cdn-icons-png.flaticon.com/512/3135/3135715.png"
        img_perfil    = ft.Image(src=IMG_DEFECTO, width=110, height=110,
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
            label="Buscar por matricula o apellido",
            width=350, prefix_icon=ft.Icons.SEARCH
        )

        # NUEVO PATRON para Flet 0.85+:
        # FilePicker se crea DENTRO del handler async y se llama con await.
        # No requiere page.overlay ni page.add() previo.
        async def abrir_selector_foto(e):
            nonlocal ruta_foto_seleccionada
            try:
                # Crear una instancia nueva cada vez y llamar con await
                files = await ft.FilePicker().pick_files(
                    allow_multiple=False,
                    file_type="image"
                )
                if files:
                    ext = os.path.splitext(files[0].path)[1].lower()
                    if ext in ['.jpg', '.jpeg', '.png', '.bmp']:
                        ruta_foto_seleccionada = files[0].path
                        img_perfil.src = ruta_foto_seleccionada
                        img_perfil.update()
                        mostrar_mensaje("Foto seleccionada", ft.Colors.PURPLE)
                    else:
                        mostrar_mensaje("Formato invalido (.png .jpg .jpeg .bmp)",
                                        ft.Colors.PINK_400)
            except Exception as ex:
                print(f"Error al seleccionar foto: {ex}")
                mostrar_mensaje(f"Error al abrir selector: {ex}", ft.Colors.PINK_400)

        # Limpiar
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

        # Cargar tabla
        def cargar_alumnos(busqueda=""):
            contenedor_tabla.content.controls.clear()
            try:
                temp_db = DatabaseManager()
                if busqueda:
                    alumnos = temp_db.execute_query("""
                        SELECT matricula, apellido_paterno, apellido_materno,
                               nombre, curp, telefono, especialidad,
                               estado, disciplina, foto_ruta, ciudad_origen
                        FROM alumnos
                        WHERE matricula LIKE %s OR apellido_paterno LIKE %s
                        ORDER BY matricula
                    """, (f"%{busqueda}%", f"%{busqueda}%"))
                else:
                    alumnos = temp_db.execute_query("""
                        SELECT matricula, apellido_paterno, apellido_materno,
                               nombre, curp, telefono, especialidad,
                               estado, disciplina, foto_ruta, ciudad_origen
                        FROM alumnos ORDER BY matricula
                    """)
                temp_db.close()

                if not alumnos:
                    contenedor_tabla.content.controls.append(
                        ft.Container(
                            content=ft.Text("No hay alumnos registrados",
                                            color=ft.Colors.GREY_500, size=14),
                            alignment=ft.Alignment(0, 0), padding=40
                        )
                    )
                else:
                    contenedor_tabla.content.controls.append(
                        ft.Container(
                            content=ft.Row([
                                ft.Text("Foto",       weight=ft.FontWeight.BOLD,
                                        size=13, color=ft.Colors.PURPLE_700, width=60),
                                ft.Text("Matricula",  weight=ft.FontWeight.BOLD,
                                        size=13, color=ft.Colors.PURPLE_700, width=100),
                                ft.Text("A. Paterno", weight=ft.FontWeight.BOLD,
                                        size=13, color=ft.Colors.PURPLE_700, width=110),
                                ft.Text("A. Materno", weight=ft.FontWeight.BOLD,
                                        size=13, color=ft.Colors.PURPLE_700, width=110),
                                ft.Text("Nombre(s)",  weight=ft.FontWeight.BOLD,
                                        size=13, color=ft.Colors.PURPLE_700, width=130),
                                ft.Text("CURP",       weight=ft.FontWeight.BOLD,
                                        size=13, color=ft.Colors.PURPLE_700, width=150),
                                ft.Text("Telefono",   weight=ft.FontWeight.BOLD,
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
                                lbl_resultado.value = f"Editando: {a[0]}"
                                page.update()

                            def eliminar(e):
                                def cerrar():
                                    dialogo.open = False
                                    page.update()

                                def confirmar():
                                    try:
                                        temp_db = DatabaseManager()
                                        result = temp_db.execute_query(
                                            "SELECT foto_ruta FROM alumnos WHERE matricula=%s",
                                            (a[0],)
                                        )
                                        if result and result[0][0] and \
                                           os.path.exists(result[0][0]):
                                            try: os.remove(result[0][0])
                                            except: pass
                                        temp_db.execute_query(
                                            "DELETE FROM alumnos WHERE matricula=%s",
                                            (a[0],)
                                        )
                                        temp_db.close()
                                    except Exception as ex:
                                        print(f"Error al eliminar: {ex}")
                                    dialogo.open = False
                                    page.update()
                                    mostrar_mensaje("Registro eliminado",
                                                    ft.Colors.PINK_400)
                                    cargar_alumnos(txt_buscador.value)
                                    limpiar()

                                dialogo = ft.AlertDialog(
                                    modal=True,
                                    title=ft.Text("Confirmar eliminacion"),
                                    content=ft.Text(
                                        f"Eliminar permanentemente al alumno {a[0]}?"),
                                    actions=[
                                        ft.TextButton("Cancelar",
                                                      on_click=lambda _: cerrar()),
                                        ft.Button("Eliminar",
                                                  on_click=lambda _: confirmar(),
                                                  bgcolor=ft.Colors.PINK_400,
                                                  color=ft.Colors.WHITE),
                                    ],
                                )
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
                                                 alignment=ft.Alignment(-1, 0)),
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

        # Guardar
        def guardar(e):
            nonlocal ruta_foto_seleccionada
            if not all([txt_matricula.value, txt_apellido_paterno.value,
                        txt_apellido_materno.value, txt_nombres.value,
                        txt_curp.value, txt_especialidad.value,
                        txt_telefono.value, txt_ciudad.value, txt_estado.value]):
                mostrar_mensaje("Complete todos los campos obligatorios (*)",
                                ft.Colors.PINK_400); return
            if not validar_curp(txt_curp.value):
                mostrar_mensaje("CURP invalida (18 caracteres)",
                                ft.Colors.PINK_400); return
            if not validar_telefono(txt_telefono.value):
                mostrar_mensaje("Telefono debe tener 10 digitos",
                                ft.Colors.PINK_400); return

            ruta_final = None
            if ruta_foto_seleccionada and os.path.exists(ruta_foto_seleccionada):
                ruta_final = manejar_foto(ruta_foto_seleccionada,
                                          txt_matricula.value.upper())
            try:
                temp_db = DatabaseManager()
                temp_db.execute_query("""
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
                temp_db.close()
                mostrar_mensaje("Alumno registrado correctamente", ft.Colors.PURPLE)
                limpiar()
                cargar_alumnos(txt_buscador.value)
            except mysql.connector.IntegrityError:
                mostrar_mensaje("Error: matricula o CURP ya existen.",
                                ft.Colors.PINK_400)
            except Exception as ex:
                mostrar_mensaje(f"Error al guardar: {ex}", ft.Colors.PINK_400)

        # Actualizar
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
                mostrar_mensaje("CURP invalida", ft.Colors.PINK_400); return
            if not validar_telefono(txt_telefono.value):
                mostrar_mensaje("Telefono debe tener 10 digitos",
                                ft.Colors.PINK_400); return

            ruta_final = ruta_foto_seleccionada
            if (ruta_foto_seleccionada and os.path.exists(ruta_foto_seleccionada)
                    and CARPETA_FOTOS not in ruta_foto_seleccionada):
                ruta_final = manejar_foto(ruta_foto_seleccionada, selected_matricula)

            try:
                temp_db = DatabaseManager()
                temp_db.execute_query("""
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
                temp_db.close()
                mostrar_mensaje("Alumno actualizado correctamente", ft.Colors.PURPLE)
                limpiar()
                cargar_alumnos(txt_buscador.value)
            except Exception as ex:
                mostrar_mensaje(f"Error al actualizar: {ex}", ft.Colors.PINK_400)

        def salir(e):
            page.window.close()

        txt_buscador.on_change = lambda _: cargar_alumnos(txt_buscador.value)

        # Layout
        header = ft.Container(
            content=ft.Row([
                ft.Row([
                    ft.Icon(ft.Icons.SCHOOL, color=ft.Colors.WHITE),
                    ft.Text("Sistema de Gestion de Alumnos", size=20,
                            weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                ]),
                ft.Row([
                    ft.Text(f"Usuario: {current_user}", size=13,
                            color=ft.Colors.PURPLE_100),
                    ft.IconButton(icon=ft.Icons.LOGOUT,
                                  icon_color=ft.Colors.WHITE,
                                  tooltip="Cerrar sesion",
                                  on_click=lambda _: ir_login()),
                ])
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            padding=15, bgcolor=ft.Colors.PURPLE, border_radius=15
        )

        form_card = ft.Container(
            content=ft.Row([
                ft.Column([
                    ft.Text("DATOS DEL ALUMNO", size=16,
                            weight=ft.FontWeight.BOLD, color=ft.Colors.PURPLE_700),
                    ft.Row([txt_matricula, txt_apellido_paterno,
                            txt_apellido_materno], spacing=15),
                    ft.Row([txt_nombres, txt_curp, txt_especialidad], spacing=15),
                    ft.Row([txt_telefono, txt_ciudad, txt_estado], spacing=15),
                    ft.Row([txt_disciplina], spacing=15),
                    ft.Divider(height=5, color=ft.Colors.TRANSPARENT),
                    ft.Row([
                        ft.Button("Guardar", on_click=guardar,
                                  width=130, bgcolor=ft.Colors.PURPLE,
                                  color=ft.Colors.WHITE),
                        ft.Button("Actualizar", on_click=actualizar,
                                  width=130, bgcolor=ft.Colors.PURPLE_300,
                                  color=ft.Colors.WHITE),
                        ft.Button("Limpiar", on_click=limpiar,
                                  width=130, bgcolor=ft.Colors.PURPLE_100,
                                  color=ft.Colors.PURPLE_700),
                        ft.Button("Salir", on_click=salir,
                                  width=130, bgcolor=ft.Colors.PINK_400,
                                  color=ft.Colors.WHITE),
                    ], spacing=10),
                    lbl_resultado,
                ], spacing=12, expand=True),

                ft.VerticalDivider(width=20, color=ft.Colors.PURPLE_50),

                ft.Column([
                    ft.Text("FOTO PERFIL", size=14,
                            weight=ft.FontWeight.BOLD, color=ft.Colors.PURPLE_700),
                    ft.Container(
                        content=img_perfil,
                        border=ft.Border.all(2, ft.Colors.PURPLE_200),
                        border_radius=60, padding=4
                    ),
                    ft.Button(
                        "Cargar Foto",
                        icon=ft.Icons.UPLOAD_FILE,
                        # handler async directo - patron oficial Flet 0.85+
                        on_click=abrir_selector_foto,
                        bgcolor=ft.Colors.PURPLE_50,
                        color=ft.Colors.PURPLE,
                    ),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                   spacing=10, width=170),
            ]),
            padding=25, bgcolor=ft.Colors.WHITE, border_radius=20,
            shadow=ft.BoxShadow(blur_radius=10, color=SHADOW_COLOR)
        )

        panel = ft.Container(
            content=ft.Column([
                header,
                form_card,
                ft.Container(
                    content=ft.Row([txt_buscador],
                                   alignment=ft.MainAxisAlignment.END),
                    padding=5
                ),
                contenedor_tabla,
            ], spacing=15),
            padding=ft.Padding(left=20, right=20, top=15, bottom=15)
        )

        navegar(
            ft.Row([panel], expand=True),
            1350, 850,
            ft.CrossAxisAlignment.START,
            ft.MainAxisAlignment.START,
            "auto"
        )
        cargar_alumnos()

    # Arranque
    ir_login()


if __name__ == "__main__":
    ft.run(main)