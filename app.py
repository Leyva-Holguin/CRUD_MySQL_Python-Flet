import flet as ft
import mysql.connector
import bcrypt
import re
import os
import shutil
import sys

def main(page: ft.Page):
    page.title = "Sistema de Gestión de Alumnos"
    page.bgcolor = ft.Colors.PURPLE_50
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.window.width = 1350
    page.window.height = 850
    page.theme_mode = ft.ThemeMode.LIGHT
    page.theme = ft.Theme(
        color_scheme=ft.ColorScheme(
            primary=ft.Colors.PURPLE,
            primary_container=ft.Colors.PURPLE_100,
            secondary=ft.Colors.PINK,
            secondary_container=ft.Colors.PINK_100,
        ),
    )

    current_user = None
    conexion_db = None
    cursor_db = None
    selected_matricula = None
    ruta_foto_seleccionada = ""  
    CARPETA_FOTOS = "fotos_perfil"
    
    if not os.path.exists(CARPETA_FOTOS):
        os.makedirs(CARPETA_FOTOS)
        
    try:
        conexion_db = mysql.connector.connect(
            host="localhost",
            user="root",
            password=""
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
            password_hash = bcrypt.hashpw("admin123".encode('utf-8'), salt)
            cursor_db.execute("INSERT INTO usuarios (username, password_hash) VALUES (%s, %s)", ("admin", password_hash))

        conexion_db.commit()

    except Exception as e:
        print(f"Error de conexión inicial a MySQL: {e}")
        return

    def mostrar_mensaje(texto, color):
        # API Actual: Los Snacks se gestionan mediante page.open()
        snack = ft.SnackBar(content=ft.Text(texto, color=ft.Colors.WHITE), bgcolor=color, duration=3000)
        page.overlay.append(snack)
        page.open(snack)

    def validar_curp(curp):
        patron = r'^[A-Z]{4}\d{6}[A-Z]{6}\d{2}$'
        return bool(re.match(patron, curp.upper()))

    def validar_telefono(telefono):
        return bool(re.match(r'^\d{10}$', telefono))

    def mostrar_login():
        page.controls.clear()
        page.scroll = None
        page.window.width = 480
        page.window.height = 600
        page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        page.vertical_alignment = ft.MainAxisAlignment.CENTER
        
        txt_usuario = ft.TextField(label="Usuario", width=320, prefix_icon=ft.Icons.PERSON, autofocus=True, border_color=ft.Colors.PURPLE_200, focused_border_color=ft.Colors.PURPLE)
        txt_password = ft.TextField(label="Contraseña", width=320, password=True, can_reveal_password=True, prefix_icon=ft.Icons.LOCK, border_color=ft.Colors.PURPLE_200, focused_border_color=ft.Colors.PURPLE)
        lbl_error = ft.Text("", color=ft.Colors.PINK_400, size=12)
        
        def iniciar_sesion(e):
            usuario = txt_usuario.value
            password = txt_password.value
            if not usuario or not password:
                lbl_error.value = "Complete todos los campos"
                page.update()
                return
            try:
                cursor_db.execute("SELECT password_hash FROM usuarios WHERE username = %s", (usuario,))
                resultado = cursor_db.fetchone()
                if resultado:
                    password_hash = resultado[0]
                    b_password = password.encode('utf-8')
                    b_hash = password_hash if isinstance(password_hash, bytes) else password_hash.encode('utf-8')
                    if bcrypt.checkpw(b_password, b_hash):
                        nonlocal current_user
                        current_user = usuario
                        mostrar_panel_principal()
                        return
                lbl_error.value = "Usuario o contraseña incorrectos"
                page.update()
            except Exception as ex:
                lbl_error.value = f"Error: {str(ex)}"
                page.update()
                
        login_card = ft.Container(
            content=ft.Column(
                [
                    ft.Icon(ft.Icons.SCHOOL, size=70, color=ft.Colors.PURPLE),
                    ft.Text("SISTEMA DE GESTIÓN", size=24, weight=ft.FontWeight.BOLD, color=ft.Colors.PURPLE_700),
                    ft.Text("DE ALUMNOS", size=20, weight=ft.FontWeight.W_500, color=ft.Colors.PURPLE_400),
                    ft.Divider(height=30, color=ft.Colors.PURPLE_100),
                    txt_usuario, txt_password, lbl_error,
                    ft.ElevatedButton("INGRESAR", on_click=iniciar_sesion, width=320, height=45, bgcolor=ft.Colors.PURPLE, color=ft.Colors.WHITE),
                    ft.TextButton("Crear cuenta nueva", on_click=lambda _: mostrar_registro()),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=15
            ),
            width=420, padding=40, bgcolor=ft.Colors.WHITE, border_radius=30,
            shadow=ft.BoxShadow(blur_radius=15, color=ft.Colors.with_opacity(0.1, ft.Colors.BLACK))
        )
        page.add(login_card)
        page.update()

    def mostrar_registro():
        page.controls.clear()
        page.scroll = None
        txt_nuevo_usuario = ft.TextField(label="Nuevo Usuario", width=320, prefix_icon=ft.Icons.PERSON, autofocus=True, border_color=ft.Colors.PURPLE_200, focused_border_color=ft.Colors.PURPLE)
        txt_nueva_pass = ft.TextField(label="Contraseña", width=320, password=True, can_reveal_password=True, prefix_icon=ft.Icons.LOCK, border_color=ft.Colors.PURPLE_200, focused_border_color=ft.Colors.PURPLE)
        txt_confirmar_pass = ft.TextField(label="Confirmar Contraseña", width=320, password=True, can_reveal_password=True, prefix_icon=ft.Icons.LOCK, border_color=ft.Colors.PURPLE_200, focused_border_color=ft.Colors.PURPLE)
        lbl_reg_error = ft.Text("", color=ft.Colors.PINK_400, size=12)

        def registrar_usuario(e):
            usuario = txt_nuevo_usuario.value
            password = txt_nueva_pass.value
            confirmar = txt_confirmar_pass.value

            if not usuario or not password:
                lbl_reg_error.value = "Complete todos los campos"
                page.update()
                return
            if password != confirmar:
                lbl_reg_error.value = "Las contraseñas no coinciden"
                page.update()
                return
            try:
                salt = bcrypt.gensalt()
                password_hash = bcrypt.hashpw(password.encode('utf-8'), salt)
                cursor_db.execute("INSERT INTO usuarios (username, password_hash) VALUES (%s, %s)", (usuario, password_hash))
                conexion_db.commit()
                mostrar_mensaje(f"Usuario {usuario} creado exitosamente", ft.Colors.PURPLE)
                mostrar_login()
            except mysql.connector.IntegrityError:
                lbl_reg_error.value = "El usuario ya existe"
                page.update()

        page.add(
            ft.Container(
                content=ft.Column(
                    [
                        ft.Icon(ft.Icons.SCHOOL, size=60, color=ft.Colors.PURPLE),
                        ft.Text("CREAR NUEVA CUENTA", size=28, weight=ft.FontWeight.BOLD, color=ft.Colors.PURPLE_700),
                        ft.Divider(height=20, color=ft.Colors.PURPLE_100),
                        txt_nuevo_usuario, txt_nueva_pass, txt_confirmar_pass, lbl_reg_error,
                        ft.ElevatedButton("Registrar", on_click=registrar_usuario, width=320, height=45, bgcolor=ft.Colors.PURPLE, color=ft.Colors.WHITE),
                        ft.TextButton("Volver al Login", on_click=lambda _: mostrar_login()),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=15
                ),
                width=420, padding=40, bgcolor=ft.Colors.WHITE, border_radius=30,
                shadow=ft.BoxShadow(blur_radius=15, color=ft.Colors.with_opacity(0.1, ft.Colors.BLACK))
            )
        )
        page.update()

    def mostrar_panel_principal():
        page.controls.clear()
        page.scroll = ft.ScrollMode.ALWAYS 
        page.window.width = 1350
        page.window.height = 850
        page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        page.vertical_alignment = ft.MainAxisAlignment.START

        filtro_letras = ft.InputFilter(allow=True, regex_string=r"[a-zA-ZáéíóúÁÉÍÓÚñÑ ]", replacement_string="")
        filtro_numeros = ft.InputFilter(allow=True, regex_string=r"[0-9]", replacement_string="")

        txt_matricula = ft.TextField(label="Matrícula *", width=220)
        txt_apellido_paterno = ft.TextField(label="Apellido Paterno *", input_filter=filtro_letras, width=220)
        txt_apellido_materno = ft.TextField(label="Apellido Materno *", input_filter=filtro_letras, width=220)
        txt_nombres = ft.TextField(label="Nombre(s) *", input_filter=filtro_letras, width=220)
        txt_curp = ft.TextField(label="CURP *", max_length=18, width=220)
        txt_especialidad = ft.TextField(label="Especialidad *", input_filter=filtro_letras, width=220)
        txt_telefono = ft.TextField(label="Teléfono *", max_length=10, input_filter=filtro_numeros, width=220)
        txt_ciudad = ft.TextField(label="Ciudad de Origen *", input_filter=filtro_letras, width=220)
        
        # MEJORA: Cambio de TextField a Dropdown (Catálogo Estático de Estados)
        txt_estado = ft.Dropdown(
            label="Estado *", 
            width=220,
            options=[
                ft.dropdown.Option("CHIHUAHUA"),
                ft.dropdown.Option("NUEVO LEÓN"),
                ft.dropdown.Option("JALISCO"),
                ft.dropdown.Option("CIUDAD DE MÉXICO"),
                ft.dropdown.Option("SONORA"),
                ft.dropdown.Option("COAHUILA")
            ]
        )
        
        # MEJORA: Cambio de TextField a Dropdown (Disciplinas Deportivas)
        txt_disciplina = ft.Dropdown(
            label="Disciplina Deportiva", 
            width=220,
            options=[
                ft.dropdown.Option("FÚTBOL"),
                ft.dropdown.Option("BÁSQUETBOL"),
                ft.dropdown.Option("VÓLEIBOL"),
                ft.dropdown.Option("ATLETISMO"),
                ft.dropdown.Option("NINGUNA")
            ]
        )

        IMG_DEFECTO = "https://cdn-icons-png.flaticon.com/512/3135/3135715.png"
        img_perfil = ft.Image(src=IMG_DEFECTO, width=110, height=110, fit=ft.ImageFit.COVER, border_radius=55)

        lbl_resultado = ft.Text("", size=12)
        contenedor_tabla = ft.Container(
            content=ft.Column(scroll=ft.ScrollMode.AUTO),
            height=280, bgcolor=ft.Colors.WHITE, border_radius=15, padding=20,
            border=ft.border.all(1, ft.Colors.PURPLE_100),
        )
        
        txt_buscador = ft.TextField(label="Buscar por matrícula o apellido", width=350, prefix_icon=ft.Icons.SEARCH)

        def al_seleccionar_archivo(e: ft.FilePickerResultEvent):
            nonlocal ruta_foto_seleccionada
            if e.files:
                ext = os.path.splitext(e.files[0].path)[1].lower()
                if ext in ['.jpg', '.jpeg', '.png', '.bmp']:
                    ruta_foto_seleccionada = e.files[0].path
                    img_perfil.src = ruta_foto_seleccionada
                    img_perfil.update()
                    mostrar_mensaje("Foto seleccionada correctamente", ft.Colors.PURPLE)
                else:
                    mostrar_mensaje("Formato de imagen inválido (.png, .jpg, .jpeg)", ft.Colors.PINK_400)

        file_picker = ft.FilePicker(on_result=al_seleccionar_archivo)
        page.overlay.append(file_picker)

        def limpiar_formulario(e):
            nonlocal selected_matricula, ruta_foto_seleccionada
            txt_matricula.value = ""
            txt_matricula.disabled = False
            txt_apellido_paterno.value = ""
            txt_apellido_materno.value = ""
            txt_nombres.value = ""
            txt_curp.value = ""
            txt_especialidad.value = ""
            txt_telefono.value = ""
            txt_ciudad.value = ""
            txt_estado.value = None
            txt_disciplina.value = None
            selected_matricula = None
            ruta_foto_seleccionada = ""
            img_perfil.src = IMG_DEFECTO
            lbl_resultado.value = ""
            txt_matricula.focus()
            page.update()

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
                        FROM alumnos
                        ORDER BY matricula
                    """)
                alumnos = cursor_db.fetchall()
                
                if not alumnos:
                    contenedor_tabla.content.controls.append(
                        ft.Container(
                            content=ft.Text("No hay alumnos registrados", color=ft.Colors.GREY_500, size=14, weight=ft.FontWeight.W_500), 
                            alignment=ft.alignment.center, padding=40
                        )
                    )
                else:
                    encabezados = ft.Container(
                        content=ft.Row([
                            ft.Text("Foto", weight=ft.FontWeight.BOLD, size=13, color=ft.Colors.PURPLE_700, width=60),
                            ft.Text("Matrícula", weight=ft.FontWeight.BOLD, size=13, color=ft.Colors.PURPLE_700, width=100),
                            ft.Text("A. Paterno", weight=ft.FontWeight.BOLD, size=13, color=ft.Colors.PURPLE_700, width=110),
                            ft.Text("A. Materno", weight=ft.FontWeight.BOLD, size=13, color=ft.Colors.PURPLE_700, width=110),
                            ft.Text("Nombre(s)", weight=ft.FontWeight.BOLD, size=13, color=ft.Colors.PURPLE_700, width=130),
                            ft.Text("CURP", weight=ft.FontWeight.BOLD, size=13, color=ft.Colors.PURPLE_700, width=150),
                            ft.Text("Teléfono", weight=ft.FontWeight.BOLD, size=13, color=ft.Colors.PURPLE_700, width=90),
                            ft.Text("Acciones", weight=ft.FontWeight.BOLD, size=13, color=ft.Colors.PURPLE_700, width=100),
                        ], spacing=10),
                        padding=ft.padding.only(bottom=10),
                    )
                    contenedor_tabla.content.controls.append(encabezados)
                    contenedor_tabla.content.controls.append(ft.Divider(color=ft.Colors.PURPLE_100, height=1))
                    
                    for reg in alumnos:
                        def crear_fila(alumno_data):
                            def editar_click(e):
                                nonlocal selected_matricula, ruta_foto_seleccionada
                                selected_matricula = alumno_data[0]
                                txt_matricula.value = alumno_data[0]
                                txt_matricula.disabled = True
                                txt_apellido_paterno.value = alumno_data[1]
                                txt_apellido_materno.value = alumno_data[2]
                                txt_nombres.value = alumno_data[3]
                                txt_curp.value = alumno_data[4]
                                txt_telefono.value = alumno_data[5]
                                txt_especialidad.value = alumno_data[6]
                                txt_estado.value = alumno_data[7]       
                                txt_disciplina.value = alumno_data[8] if alumno_data[8] else "NINGUNA" 
                                txt_ciudad.value = alumno_data[10]
                                
                                if alumno_data[9] and os.path.exists(alumno_data[9]):
                                    ruta_foto_seleccionada = alumno_data[9]
                                    img_perfil.src = alumno_data[9]
                                else:
                                    ruta_foto_seleccionada = ""
                                    img_perfil.src = IMG_DEFECTO
                                
                                lbl_resultado.value = f"Editando: {alumno_data[0]}"
                                page.update()
                            
                            def eliminar_click(e):
                                def confirmar_eliminar(ev):
                                    cursor_db.execute("SELECT foto_ruta FROM alumnos WHERE matricula = %s", (alumno_data[0],))
                                    res_foto = cursor_db.fetchone()
                                    if res_foto and res_foto[0] and os.path.exists(res_foto[0]):
                                        try: os.remove(res_foto[0])
                                        except: pass

                                    cursor_db.execute("DELETE FROM alumnos WHERE matricula = %s", (alumno_data[0],))
                                    conexion_db.commit()
                                    mostrar_mensaje(f"Registro eliminado", ft.Colors.PINK_400)
                                    cargar_alumnos(txt_buscador.value)
                                    limpiar_formulario(None)
                                    page.close(dialogo) # API Actual para cerrar Overlays

                                dialogo = ft.AlertDialog(
                                    title=ft.Text("Confirmar eliminación"),
                                    content=ft.Text(f"¿Desea eliminar de forma permanente al alumno {alumno_data[0]}?"),
                                    actions=[
                                        ft.TextButton("Cancelar", on_click=lambda _: page.close(dialogo)),
                                        ft.ElevatedButton("Eliminar", on_click=confirmar_eliminar, bgcolor=ft.Colors.PINK_400, color=ft.Colors.WHITE),
                                    ],
                                )
                                page.open(dialogo) # API Actual para abrir Overlays

                            foto_src = alumno_data[9] if alumno_data[9] and os.path.exists(alumno_data[9]) else IMG_DEFECTO
                            mini_foto = ft.Image(src=foto_src, width=30, height=30, fit=ft.ImageFit.COVER, border_radius=15)

                            return ft.Container(
                                content=ft.Row([
                                    ft.Container(content=mini_foto, width=60, alignment=ft.alignment.center_left),
                                    ft.Text(str(alumno_data[0]), size=12, width=100),
                                    ft.Text(str(alumno_data[1]), size=12, width=110),
                                    ft.Text(str(alumno_data[2]), size=12, width=110),
                                    ft.Text(str(alumno_data[3]), size=12, width=130),
                                    ft.Text(str(alumno_data[4]), size=12, width=150),
                                    ft.Text(str(alumno_data[5]), size=12, width=90),
                                    ft.Row([
                                        ft.IconButton(icon=ft.Icons.EDIT, icon_size=18, icon_color=ft.Colors.PURPLE, on_click=editar_click),
                                        ft.IconButton(icon=ft.Icons.DELETE, icon_size=18, icon_color=ft.Colors.PINK_400, on_click=eliminar_click)
                                    ], spacing=0),
                                ], spacing=10),
                                padding=ft.padding.symmetric(vertical=5),
                            )
                        contenedor_tabla.content.controls.append(crear_fila(reg))
            except Exception as ex:
                print(f"Error al cargar la lista: {ex}")
            
            contenedor_tabla.update()
            page.update()

        def guardar_alumno(e):
            nonlocal ruta_foto_seleccionada
            if not all([txt_matricula.value, txt_apellido_paterno.value, txt_apellido_materno.value, txt_nombres.value, txt_curp.value, txt_especialidad.value, txt_telefono.value, txt_ciudad.value, txt_estado.value]):
                mostrar_mensaje("Campos obligatorios (*)", ft.Colors.PINK_400)
                return
            if not validar_curp(txt_curp.value) or not validar_telefono(txt_telefono.value):
                mostrar_mensaje("Valide CURP y formato de Teléfono", ft.Colors.PINK_400)
                return

            ruta_final_foto = None
            if ruta_foto_seleccionada and os.path.exists(ruta_foto_seleccionada):
                ext = os.path.splitext(ruta_foto_seleccionada)[1]
                nombre_archivo = f"{txt_matricula.value.upper()}{ext}"
                ruta_final_foto = os.path.join(CARPETA_FOTOS, nombre_archivo)
                shutil.copy(ruta_foto_seleccionada, ruta_final_foto)

            try:
                cursor_db.execute("""
                    INSERT INTO alumnos (matricula, apellido_paterno, apellido_materno, nombre, curp, especialidad, telefono, ciudad_origen, estado, disciplina, foto_ruta)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (txt_matricula.value.upper(), txt_apellido_paterno.value.upper(), txt_apellido_materno.value.upper(), txt_nombres.value.upper(), txt_curp.value.upper(), txt_especialidad.value.upper(), txt_telefono.value, txt_ciudad.value.upper(), txt_estado.value, txt_disciplina.value if txt_disciplina.value else None, ruta_final_foto))
                conexion_db.commit()
                mostrar_mensaje("Registro guardado", ft.Colors.PURPLE)
                limpiar_formulario(None)
                cargar_alumnos(txt_buscador.value)
            except Exception as ex:
                mostrar_mensaje(f"Error: La matrícula o CURP ya existen.", ft.Colors.PINK_400)

        def actualizar_alumno(e):
            nonlocal selected_matricula, ruta_foto_seleccionada
            if not selected_matricula:
                mostrar_mensaje("Selecciona un registro", ft.Colors.PINK_400)
                return
            if not all([txt_apellido_paterno.value, txt_apellido_materno.value, txt_nombres.value, txt_curp.value, txt_especialidad.value, txt_telefono.value, txt_ciudad.value, txt_estado.value]):
                mostrar_mensaje("Campos obligatorios (*)", ft.Colors.PINK_400)
                return
            if not validar_curp(txt_curp.value) or not validar_telefono(txt_telefono.value):
                mostrar_mensaje("Valide los formatos obligatorios", ft.Colors.PINK_400)
                return

            ruta_final_foto = ruta_foto_seleccionada
            if ruta_foto_seleccionada and os.path.exists(ruta_foto_seleccionada) and CARPETA_FOTOS not in ruta_foto_seleccionada:
                ext = os.path.splitext(ruta_foto_seleccionada)[1]
                nombre_archivo = f"{selected_matricula}{ext}"
                ruta_final_foto = os.path.join(CARPETA_FOTOS, nombre_archivo)
                shutil.copy(ruta_foto_seleccionada, ruta_final_foto)

            try:
                cursor_db.execute("""
                    UPDATE alumnos SET apellido_paterno=%s, apellido_materno=%s, nombre=%s, curp=%s, especialidad=%s, telefono=%s, ciudad_origen=%s, estado=%s, disciplina=%s, foto_ruta=%s
                    WHERE matricula=%s
                """, (txt_apellido_paterno.value.upper(), txt_apellido_materno.value.upper(), txt_nombres.value.upper(), txt_curp.value.upper(), txt_especialidad.value.upper(), txt_telefono.value, txt_ciudad.value.upper(), txt_estado.value, txt_disciplina.value if txt_disciplina.value else None, ruta_final_foto, selected_matricula))
                conexion_db.commit()
                mostrar_mensaje("Registro actualizado", ft.Colors.PURPLE)
                limpiar_formulario(None)
                cargar_alumnos(txt_buscador.value)
            except Exception as ex:
                mostrar_mensaje(f"Error al actualizar: {ex}", ft.Colors.PINK_400)

        def salir_programa(e):
            cursor_db.close()
            conexion_db.close()
            sys.exit()

        txt_buscador.on_change = lambda _: cargar_alumnos(txt_buscador.value)
        
        header = ft.Container(
            content=ft.Row([
                ft.Row([ft.Icon(ft.Icons.SCHOOL, color=ft.Colors.WHITE), ft.Text("Sistema de Gestión de Alumnos", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)]),
                ft.IconButton(icon=ft.Icons.LOGOUT, icon_color=ft.Colors.WHITE, on_click=lambda _: [setattr(page, "scroll", None), mostrar_login()])
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            padding=15, bgcolor=ft.Colors.PURPLE, border_radius=15
        )

        form_card = ft.Container(
            content=ft.Row([
                ft.Column([
                    ft.Text("DATOS DEL ALUMNO", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.PURPLE_700),
                    ft.Row([txt_matricula, txt_apellido_paterno, txt_apellido_materno], spacing=15),
                    ft.Row([txt_nombres, txt_curp, txt_especialidad], spacing=15),
                    ft.Row([txt_telefono, txt_ciudad, txt_estado], spacing=15), 
                    ft.Row([txt_disciplina], spacing=15),                        
                    ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
                    ft.Row([
                        ft.ElevatedButton("Guardar", on_click=guardar_alumno, bgcolor=ft.Colors.PURPLE, color=ft.Colors.WHITE, width=120),
                        ft.ElevatedButton("Actualizar", on_click=actualizar_alumno, bgcolor=ft.Colors.PURPLE_300, color=ft.Colors.WHITE, width=120),
                        ft.ElevatedButton("Limpiar", on_click=limpiar_formulario, bgcolor=ft.Colors.PURPLE_100, color=ft.Colors.PURPLE_700, width=120),
                        ft.ElevatedButton("Salir", on_click=salir_programa, bgcolor=ft.Colors.PINK_400, color=ft.Colors.WHITE, width=120)
                    ], spacing=15),
                    lbl_resultado
                ], spacing=12, expand=True),
                
                ft.VerticalDivider(width=20, color=ft.Colors.PURPLE_50),
                ft.Column([
                    ft.Text("FOTO PERFIL", size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.PURPLE_700),
                    ft.Container(content=img_perfil, border=ft.border.all(2, ft.Colors.PURPLE_200), border_radius=60, padding=4),
                    ft.ElevatedButton(
                        "Cargar Foto",
                        icon=ft.Icons.UPLOAD_FILE,
                        on_click=lambda _: file_picker.pick_files(allow_multiple=False, file_type=ft.FilePickerFileType.IMAGE),
                        bgcolor=ft.Colors.PURPLE_50,
                        color=ft.Colors.PURPLE
                    )
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10, width=160)
            ]),
            padding=25, bgcolor=ft.Colors.WHITE, border_radius=20,
            shadow=ft.BoxShadow(blur_radius=10, color=ft.Colors.with_opacity(0.05, ft.Colors.BLACK))
        )

        page.add(
            ft.Column([
                header,
                form_card,
                ft.Container(content=ft.Row([txt_buscador], alignment=ft.MainAxisAlignment.END), padding=ft.padding.only(top=5)),
                contenedor_tabla
            ], spacing=15)
        )
        
        cargar_alumnos("")
        page.update()

    mostrar_login()

if __name__ == "__main__":
    ft.app(target=main)