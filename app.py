import flet as ft
import mysql.connector
import bcrypt
import re
import sys

def main(page: ft.Page):
    page.title = "Sistema de Gestion de Alumnos"
    page.bgcolor = ft.Colors.LIME_100
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.window_width = 1100
    page.window_height = 750

    current_user = None
    conexion_db = None
    cursor_db = None
    selected_matricula = None
    modo_registro = False

    try:
        conexion_db = mysql.connector.connect(
            host="localhost",
            user="root",
            password="admin123"
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
            CREATE TABLE IF NOT EXISTS estados (
                id INT PRIMARY KEY AUTO_INCREMENT,
                nombre VARCHAR(50) NOT NULL
            )
        """)

        cursor_db.execute("""
            CREATE TABLE IF NOT EXISTS disciplinas (
                id INT PRIMARY KEY AUTO_INCREMENT,
                nombre VARCHAR(100) NOT NULL
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
                estado_id INT NOT NULL,
                disciplina_id INT,
                FOREIGN KEY (estado_id) REFERENCES estados(id),
                FOREIGN KEY (disciplina_id) REFERENCES disciplinas(id)
            )
        """)

        cursor_db.execute("SELECT COUNT(*) FROM estados")
        if cursor_db.fetchone()[0] == 0:
            estados_lista = ['Jalisco', 'Nuevo Leon', 'Ciudad de Mexico', 'Veracruz', 'Puebla', 'Sonora', 'Chihuahua']
            for estado in estados_lista:
                cursor_db.execute("INSERT INTO estados (nombre) VALUES (%s)", (estado,))

        cursor_db.execute("SELECT COUNT(*) FROM disciplinas")
        if cursor_db.fetchone()[0] == 0:
            disciplinas_lista = ['Futbol', 'Basquetbol', 'Voleibol', 'Natacion', 'Atletismo', 'Tenis', 'Boxeo', 'Taekwondo']
            for disciplina in disciplinas_lista:
                cursor_db.execute("INSERT INTO disciplinas (nombre) VALUES (%s)", (disciplina,))

        cursor_db.execute("SELECT COUNT(*) FROM usuarios")
        if cursor_db.fetchone()[0] == 0:
            salt = bcrypt.gensalt()
            password_hash = bcrypt.hashpw("admin123".encode('utf-8'), salt)
            cursor_db.execute(
                "INSERT INTO usuarios (username, password_hash) VALUES (%s, %s)",
                ("admin", password_hash)
            )

        conexion_db.commit()

    except Exception as e:
        print(f"Error de conexion: {e}")
        return

    def mostrar_mensaje(texto, color):
        snack = ft.SnackBar(content=ft.Text(texto), bgcolor=color, duration=3000)
        page.snack_bar = snack
        snack.open = True
        page.update()

    def validar_curp(curp):
        patron = r'^[A-Z]{4}\d{6}[A-Z]{6}\d{2}$'
        return bool(re.match(patron, curp.upper()))

    def validar_telefono(telefono):
        return bool(re.match(r'^\d{10}$', telefono))

    def mostrar_login():
        page.controls.clear()
        page.window_width = 450
        page.window_height = 550

        txt_usuario = ft.TextField(label="Usuario", width=300, prefix_icon=ft.Icons.PERSON, autofocus=True)
        txt_password = ft.TextField(label="Contrasena", width=300, password=True, can_reveal_password=True, prefix_icon=ft.Icons.LOCK)
        lbl_error = ft.Text("", color=ft.Colors.RED_400, size=12)

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
                    password_hash = resultado[0] if isinstance(resultado, tuple) else resultado['password_hash']
                    if bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8')):
                        nonlocal current_user
                        current_user = usuario
                        mostrar_panel_principal()
                        return
                lbl_error.value = "Usuario o contrasena incorrectos"
                page.update()
            except Exception as ex:
                lbl_error.value = f"Error: {str(ex)}"
                page.update()

        def mostrar_registro(e):
            nonlocal modo_registro
            modo_registro = True
            page.controls.clear()
            
            txt_nuevo_usuario = ft.TextField(label="Nuevo Usuario", width=300, prefix_icon=ft.Icons.PERSON, autofocus=True)
            txt_nueva_pass = ft.TextField(label="Contrasena", width=300, password=True, can_reveal_password=True, prefix_icon=ft.Icons.LOCK)
            txt_confirmar_pass = ft.TextField(label="Confirmar Contrasena", width=300, password=True, can_reveal_password=True, prefix_icon=ft.Icons.LOCK)
            lbl_reg_error = ft.Text("", color=ft.Colors.RED_400, size=12)

            def registrar_usuario(e):
                usuario = txt_nuevo_usuario.value
                password = txt_nueva_pass.value
                confirmar = txt_confirmar_pass.value

                if not usuario or not password:
                    lbl_reg_error.value = "Complete todos los campos"
                    page.update()
                    return
                if password != confirmar:
                    lbl_reg_error.value = "Las contrasenas no coinciden"
                    page.update()
                    return
                if len(password) < 4:
                    lbl_reg_error.value = "La contrasena debe tener al menos 4 caracteres"
                    page.update()
                    return
                try:
                    salt = bcrypt.gensalt()
                    password_hash = bcrypt.hashpw(password.encode('utf-8'), salt)
                    cursor_db.execute(
                        "INSERT INTO usuarios (username, password_hash) VALUES (%s, %s)",
                        (usuario, password_hash)
                    )
                    conexion_db.commit()
                    mostrar_mensaje(f"Usuario {usuario} creado exitosamente", ft.Colors.GREEN_600)
                    volver_login(None)
                except mysql.connector.IntegrityError:
                    lbl_reg_error.value = "El usuario ya existe"
                    page.update()
                except Exception as ex:
                    lbl_reg_error.value = f"Error: {str(ex)}"
                    page.update()

            def volver_login(e):
                nonlocal modo_registro
                modo_registro = False
                mostrar_login()

            page.add(
                ft.Container(
                    content=ft.Column(
                        [ft.Text("CREAR NUEVA CUENTA", size=22, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_800),
                         ft.Divider(height=20),
                         txt_nuevo_usuario, txt_nueva_pass, txt_confirmar_pass, lbl_reg_error,
                         ft.ElevatedButton("Registrar", on_click=registrar_usuario, width=300, bgcolor=ft.Colors.GREEN_600, color=ft.Colors.WHITE),
                         ft.TextButton("Volver al Login", on_click=volver_login)],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=15
                    ),
                    width=400, padding=30, bgcolor=ft.Colors.WHITE, border_radius=20
                )
            )
            page.update()

        btn_login = ft.ElevatedButton("Ingresar", on_click=iniciar_sesion, width=300, icon=ft.Icons.LOGIN, bgcolor=ft.Colors.BLUE_700, color=ft.Colors.WHITE)
        btn_registro = ft.TextButton("Crear cuenta nueva", on_click=mostrar_registro)

        page.add(
            ft.Container(
                content=ft.Column(
                    [ft.Text("SISTEMA DE GESTION DE ALUMNOS", size=22, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_800),
                     ft.Text("Iniciar Sesion", size=16, color=ft.Colors.GREY_600),
                     ft.Divider(height=20),
                     txt_usuario, txt_password, lbl_error, btn_login, btn_registro],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=15
                ),
                width=400, padding=30, bgcolor=ft.Colors.WHITE, border_radius=20
            )
        )
        page.update()

    def mostrar_panel_principal():
        page.controls.clear()
        page.window_width = 1200
        page.window_height = 750

        cursor_db.execute("SELECT id, nombre FROM estados ORDER BY nombre")
        estados = cursor_db.fetchall()
        cursor_db.execute("SELECT id, nombre FROM disciplinas ORDER BY nombre")
        disciplinas = cursor_db.fetchall()

        txt_matricula = ft.TextField(label="Matricula *", width=180, autofocus=True)
        txt_apellido_paterno = ft.TextField(label="Apellido Paterno *", width=180)
        txt_apellido_materno = ft.TextField(label="Apellido Materno *", width=180)
        txt_nombres = ft.TextField(label="Nombre(s) *", width=180)
        txt_curp = ft.TextField(label="CURP *", width=220, max_length=18)
        txt_especialidad = ft.TextField(label="Especialidad *", width=220)
        txt_telefono = ft.TextField(label="Telefono *", width=180, max_length=10)
        txt_ciudad = ft.TextField(label="Ciudad de Origen *", width=180)

        drop_estado = ft.Dropdown(label="Estado *", width=200, options=[ft.dropdown.Option(str(e[0]), e[1]) for e in estados])
        drop_disciplina = ft.Dropdown(label="Disciplina Deportiva", width=220, options=[ft.dropdown.Option(str(d[0]), d[1]) for d in disciplinas])

        lbl_resultado = ft.Text("", size=12)
        
        contenedor_tabla = ft.Container(content=ft.Column(scroll=ft.ScrollMode.AUTO), height=300, width=1000, bgcolor=ft.Colors.WHITE, border_radius=10, padding=10)
        txt_buscador = ft.TextField(label="Buscar por matricula o apellido", width=350, prefix_icon=ft.Icons.SEARCH)

        def limpiar_formulario(e):
            nonlocal selected_matricula
            txt_matricula.value = ""
            txt_matricula.disabled = False
            txt_apellido_paterno.value = ""
            txt_apellido_materno.value = ""
            txt_nombres.value = ""
            txt_curp.value = ""
            txt_especialidad.value = ""
            txt_telefono.value = ""
            txt_ciudad.value = ""
            drop_estado.value = None
            drop_disciplina.value = None
            selected_matricula = None
            lbl_resultado.value = ""
            txt_matricula.focus()
            page.update()

        def cargar_alumnos(busqueda=""):
            contenedor_tabla.content.controls.clear()
            try:
                if busqueda:
                    cursor_db.execute("""
                        SELECT a.matricula, a.apellido_paterno, a.apellido_materno,
                               a.nombre, a.curp, a.telefono, a.especialidad,
                               e.nombre as estado, d.nombre as disciplina
                        FROM alumnos a
                        LEFT JOIN estados e ON a.estado_id = e.id
                        LEFT JOIN disciplinas d ON a.disciplina_id = d.id
                        WHERE a.matricula LIKE %s OR a.apellido_paterno LIKE %s
                        ORDER BY a.matricula
                    """, (f"%{busqueda}%", f"%{busqueda}%"))
                else:
                    cursor_db.execute("""
                        SELECT a.matricula, a.apellido_paterno, a.apellido_materno,
                               a.nombre, a.curp, a.telefono, a.especialidad,
                               e.nombre as estado, d.nombre as disciplina
                        FROM alumnos a
                        LEFT JOIN estados e ON a.estado_id = e.id
                        LEFT JOIN disciplinas d ON a.disciplina_id = d.id
                        ORDER BY a.matricula
                    """)
                alumnos = cursor_db.fetchall()
                if not alumnos:
                    contenedor_tabla.content.controls.append(ft.Text("No hay registros", color=ft.Colors.GREY_600))
                else:
                    encabezados = ft.Row([
                        ft.Container(ft.Text("Matricula", weight=ft.FontWeight.BOLD, size=12), width=100),
                        ft.Container(ft.Text("Apellido Paterno", weight=ft.FontWeight.BOLD, size=12), width=120),
                        ft.Container(ft.Text("Apellido Materno", weight=ft.FontWeight.BOLD, size=12), width=120),
                        ft.Container(ft.Text("Nombre(s)", weight=ft.FontWeight.BOLD, size=12), width=120),
                        ft.Container(ft.Text("CURP", weight=ft.FontWeight.BOLD, size=12), width=150),
                        ft.Container(ft.Text("Telefono", weight=ft.FontWeight.BOLD, size=12), width=80),
                        ft.Container(ft.Text("Acciones", weight=ft.FontWeight.BOLD, size=12), width=100)
                    ], spacing=5)
                    contenedor_tabla.content.controls.append(encabezados)
                    contenedor_tabla.content.controls.append(ft.Divider(height=1))
                    for alumno in alumnos:
                        def crear_fila(a):
                            def editar_click(e):
                                nonlocal selected_matricula
                                selected_matricula = a[0]
                                txt_matricula.value = a[0]
                                txt_matricula.disabled = True
                                txt_apellido_paterno.value = a[1]
                                txt_apellido_materno.value = a[2]
                                txt_nombres.value = a[3]
                                txt_curp.value = a[4]
                                txt_telefono.value = a[5]
                                txt_especialidad.value = a[6]
                                for i, est in enumerate(estados):
                                    if est[1] == a[7]:
                                        drop_estado.value = str(est[0])
                                        break
                                for i, disc in enumerate(disciplinas):
                                    if disc[1] == a[8]:
                                        drop_disciplina.value = str(disc[0])
                                        break
                                lbl_resultado.value = f"Editando: {a[0]}"
                                lbl_resultado.color = ft.Colors.ORANGE_600
                                page.update()
                            def eliminar_click(e):
                                def confirmar_eliminar(e):
                                    try:
                                        cursor_db.execute("DELETE FROM alumnos WHERE matricula = %s", (a[0],))
                                        conexion_db.commit()
                                        mostrar_mensaje(f"Alumno {a[0]} eliminado", ft.Colors.GREEN_600)
                                        cargar_alumnos(txt_buscador.value)
                                        limpiar_formulario(None)
                                        cerrar_dialogo(None)
                                    except Exception as ex:
                                        mostrar_mensaje(f"Error: {str(ex)}", ft.Colors.RED_400)
                                def cerrar_dialogo(e):
                                    dialogo.open = False
                                    page.update()
                                dialogo = ft.AlertDialog(
                                    title=ft.Text("Confirmar eliminacion"),
                                    content=ft.Text(f"Eliminar al alumno {a[0]} - {a[3]} {a[1]}?"),
                                    actions=[
                                        ft.TextButton("Cancelar", on_click=cerrar_dialogo),
                                        ft.ElevatedButton("Eliminar", on_click=confirmar_eliminar, bgcolor=ft.Colors.RED_600)
                                    ]
                                )
                                page.dialog = dialogo
                                dialogo.open = True
                                page.update()
                            return ft.Row([
                                ft.Container(ft.Text(a[0], size=12), width=100),
                                ft.Container(ft.Text(a[1], size=12), width=120),
                                ft.Container(ft.Text(a[2], size=12), width=120),
                                ft.Container(ft.Text(a[3], size=12), width=120),
                                ft.Container(ft.Text(a[4], size=12), width=150),
                                ft.Container(ft.Text(a[5], size=12), width=80),
                                ft.Container(ft.Row([ft.IconButton(icon=ft.Icons.EDIT, icon_size=20, icon_color=ft.Colors.ORANGE_600, on_click=editar_click), ft.IconButton(icon=ft.Icons.DELETE, icon_size=20, icon_color=ft.Colors.RED_600, on_click=eliminar_click)]), width=100)
                            ], spacing=5, vertical_alignment=ft.CrossAxisAlignment.CENTER)
                        contenedor_tabla.content.controls.append(crear_fila(alumno))
            except Exception as ex:
                mostrar_mensaje(f"Error al cargar: {str(ex)}", ft.Colors.RED_400)
            page.update()

        def guardar_alumno(e):
            if not all([txt_matricula.value, txt_apellido_paterno.value, txt_apellido_materno.value, txt_nombres.value, txt_curp.value, txt_especialidad.value, txt_telefono.value, txt_ciudad.value, drop_estado.value]):
                mostrar_mensaje("Complete todos los campos obligatorios", ft.Colors.RED_400)
                return
            if not validar_curp(txt_curp.value):
                mostrar_mensaje("Formato de CURP invalido", ft.Colors.RED_400)
                return
            if not validar_telefono(txt_telefono.value):
                mostrar_mensaje("El telefono debe tener 10 digitos", ft.Colors.RED_400)
                return
            try:
                cursor_db.execute("""
                    INSERT INTO alumnos (matricula, apellido_paterno, apellido_materno, nombre,
                        curp, especialidad, telefono, ciudad_origen, estado_id, disciplina_id)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (txt_matricula.value.upper(), txt_apellido_paterno.value.upper(), txt_apellido_materno.value.upper(), txt_nombres.value.upper(), txt_curp.value.upper(), txt_especialidad.value.upper(), txt_telefono.value, txt_ciudad.value.upper(), int(drop_estado.value), int(drop_disciplina.value) if drop_disciplina.value else None))
                conexion_db.commit()
                mostrar_mensaje("Alumno guardado exitosamente", ft.Colors.GREEN_600)
                limpiar_formulario(None)
                cargar_alumnos(txt_buscador.value)
            except mysql.connector.IntegrityError as ex:
                if "Duplicate entry" in str(ex):
                    mostrar_mensaje("La matricula o CURP ya existe", ft.Colors.RED_400)
                else:
                    mostrar_mensaje(f"Error: {str(ex)}", ft.Colors.RED_400)
            except Exception as ex:
                mostrar_mensaje(f"Error: {str(ex)}", ft.Colors.RED_400)

        def actualizar_alumno(e):
            nonlocal selected_matricula
            if not selected_matricula:
                mostrar_mensaje("Seleccione un alumno para actualizar", ft.Colors.RED_400)
                return
            try:
                cursor_db.execute("""
                    UPDATE alumnos SET apellido_paterno=%s, apellido_materno=%s, nombre=%s,
                        curp=%s, especialidad=%s, telefono=%s, ciudad_origen=%s, estado_id=%s, disciplina_id=%s
                    WHERE matricula=%s
                """, (txt_apellido_paterno.value.upper(), txt_apellido_materno.value.upper(), txt_nombres.value.upper(), txt_curp.value.upper(), txt_especialidad.value.upper(), txt_telefono.value, txt_ciudad.value.upper(), int(drop_estado.value), int(drop_disciplina.value) if drop_disciplina.value else None, selected_matricula))
                conexion_db.commit()
                mostrar_mensaje("Alumno actualizado exitosamente", ft.Colors.ORANGE_600)
                limpiar_formulario(None)
                cargar_alumnos(txt_buscador.value)
            except Exception as ex:
                mostrar_mensaje(f"Error: {str(ex)}", ft.Colors.RED_400)

        def buscar_alumnos(e):
            cargar_alumnos(txt_buscador.value)

        txt_buscador.on_change = buscar_alumnos

        def cerrar_sesion(e):
            nonlocal current_user
            current_user = None
            mostrar_login()

        btn_guardar = ft.ElevatedButton("Guardar", on_click=guardar_alumno, width=100, icon=ft.Icons.SAVE)
        btn_actualizar = ft.ElevatedButton("Actualizar", on_click=actualizar_alumno, width=100, icon=ft.Icons.UPDATE)
        btn_limpiar = ft.ElevatedButton("Limpiar", on_click=limpiar_formulario, width=100, icon=ft.Icons.CLEAR)
        btn_salir_sesion = ft.ElevatedButton("Salir", on_click=cerrar_sesion, width=100, icon=ft.Icons.LOGOUT, bgcolor=ft.Colors.RED_600, color=ft.Colors.WHITE)

        fila_botones1 = ft.Row([btn_guardar, btn_actualizar], alignment=ft.MainAxisAlignment.CENTER)
        fila_botones2 = ft.Row([btn_limpiar, btn_salir_sesion], alignment=ft.MainAxisAlignment.CENTER)

        page.add(
            ft.Container(
                content=ft.Column(
                    [ft.Text(f"BIENVENIDO, {current_user.upper()}", size=22, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_800),
                     ft.Divider(height=10),
                     ft.Container(content=ft.Column([ft.Text("REGISTRO DE ALUMNOS", size=16, weight=ft.FontWeight.BOLD), ft.Row([txt_matricula, txt_apellido_paterno, txt_apellido_materno]), ft.Row([txt_nombres, txt_curp, txt_especialidad]), ft.Row([txt_telefono, txt_ciudad, drop_estado]), ft.Row([drop_disciplina]), fila_botones1, fila_botones2, lbl_resultado], spacing=10, horizontal_alignment=ft.CrossAxisAlignment.CENTER), padding=20, bgcolor=ft.Colors.GREY_100, border_radius=15),
                     ft.Divider(height=10),
                     ft.Row([txt_buscador], alignment=ft.MainAxisAlignment.END),
                     contenedor_tabla],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=10
                ),
                width=1050, padding=20, bgcolor=ft.Colors.WHITE, border_radius=15
            )
        )
        cargar_alumnos("")

    mostrar_login()

ft.app(target=main)