import flet as ft
import mysql.connector
import bcrypt
import re

def main(page: ft.Page):
    page.title = "Sistema de Gestión de Alumnos"
    page.bgcolor = ft.Colors.PURPLE_50
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.window_width = 1200
    page.window_height = 750
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

    # --- CONFIGURACIÓN E INICIALIZACIÓN DE LA BASE DE DATOS ---
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
            estados_lista = ['Aguascalientes', 'Baja California', 'Baja California Sur', 'Campeche', 'Chiapas', 'Chihuahua', 'Ciudad de México', 'Coahuila', 'Colima', 'Durango', 'Estado de México', 'Guanajuato', 'Guerrero', 'Hidalgo', 'Jalisco', 'Michoacán', 'Morelos', 'Nayarit', 'Nuevo León', 'Oaxaca', 'Puebla', 'Querétaro', 'Quintana Roo', 'San Luis Potosí', 'Sinaloa', 'Sonora', 'Tabasco', 'Tamaulipas', 'Tlaxcala', 'Veracruz', 'Yucatán', 'Zacatecas']
            for estado in estados_lista:
                cursor_db.execute("INSERT INTO estados (nombre) VALUES (%s)", (estado,))

        cursor_db.execute("SELECT COUNT(*) FROM disciplinas")
        if cursor_db.fetchone()[0] == 0:
            disciplinas_lista = ['Fútbol', 'Basquetbol', 'Voleibol', 'Natación', 'Atletismo', 'Tenis', 'Boxeo', 'Taekwondo', 'Judo', 'Gimnasia']
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
        print(f"Error de conexión inicial: {e}")
        return

    # --- FUNCIONES GENERALES DE APOYO ---
    def mostrar_mensaje(texto, color):
        snack = ft.SnackBar(
            content=ft.Text(texto, color=ft.Colors.WHITE),
            bgcolor=color,
            duration=3000,
        )
        page.overlay.append(snack)
        snack.open = True
        page.update()

    def validar_curp(curp):
        patron = r'^[A-Z]{4}\d{6}[A-Z]{6}\d{2}$'
        return bool(re.match(patron, curp.upper()))

    def validar_telefono(telefono):
        return bool(re.match(r'^\d{10}$', telefono))

    # --- INTERFAZ 1: LOGIN ---
    def mostrar_login():
        page.controls.clear()
        page.window_width = 480
        page.window_height = 600
        page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        page.vertical_alignment = ft.MainAxisAlignment.CENTER

        txt_usuario = ft.TextField(
            label="Usuario", width=320, prefix_icon=ft.Icons.PERSON,
            autofocus=True, border_color=ft.Colors.PURPLE_200, focused_border_color=ft.Colors.PURPLE,
        )
        txt_password = ft.TextField(
            label="Contraseña", width=320, password=True, can_reveal_password=True,
            prefix_icon=ft.Icons.LOCK, border_color=ft.Colors.PURPLE_200, focused_border_color=ft.Colors.PURPLE,
        )
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
        )
        page.add(login_card)
        page.update()

    # --- INTERFAZ 2: REGISTRO DE USUARIOS ---
    def mostrar_registro():
        page.controls.clear()
        
        txt_nuevo_usuario = ft.TextField(
            label="Nuevo Usuario", width=320, prefix_icon=ft.Icons.PERSON,
            autofocus=True, border_color=ft.Colors.PURPLE_200, focused_border_color=ft.Colors.PURPLE,
        )
        txt_nueva_pass = ft.TextField(
            label="Contraseña", width=320, password=True, can_reveal_password=True,
            prefix_icon=ft.Icons.LOCK, border_color=ft.Colors.PURPLE_200, focused_border_color=ft.Colors.PURPLE,
        )
        txt_confirmar_pass = ft.TextField(
            label="Confirmar Contraseña", width=320, password=True, can_reveal_password=True,
            prefix_icon=ft.Icons.LOCK, border_color=ft.Colors.PURPLE_200, focused_border_color=ft.Colors.PURPLE,
        )
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
            if len(password) < 4:
                lbl_reg_error.value = "La contraseña debe tener al menos 4 caracteres"
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
                mostrar_mensaje(f"Usuario {usuario} creado exitosamente", ft.Colors.PURPLE)
                mostrar_login()
            except mysql.connector.IntegrityError:
                lbl_reg_error.value = "El usuario ya existe"
                page.update()
            except Exception as ex:
                lbl_reg_error.value = f"Error: {str(ex)}"
                page.update()

        page.add(
            ft.Container(
                content=ft.Column(
                    [
                        ft.Icon(ft.Icons.SCHOOL, size=60, color=ft.Colors.PURPLE),
                        ft.Text("CREAR NUEVA CUENTA", size=28, weight=ft.FontWeight.BOLD, color=ft.Colors.PURPLE_700),
                        ft.Divider(height=20, color=ft.Colors.PURPLE_100),
                        txt_nuevo_usuario, txt_nueva_pass, txt_confirmar_pass,
                        lbl_reg_error,
                        ft.ElevatedButton("Registrar", on_click=registrar_usuario, width=320, height=45, bgcolor=ft.Colors.PURPLE, color=ft.Colors.WHITE),
                        ft.TextButton("Volver al Login", on_click=lambda _: mostrar_login()),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=15
                ),
                width=420, padding=40, bgcolor=ft.Colors.WHITE, border_radius=30,
            )
        )
        page.update()

    # --- INTERFAZ 3: PANEL DE CONTROL PRINCIPAL ---
    def mostrar_panel_principal():
        page.controls.clear()
        page.window_width = 1300
        page.window_height = 800
        page.horizontal_alignment = ft.CrossAxisAlignment.START
        page.vertical_alignment = ft.MainAxisAlignment.START

        cursor_db.execute("SELECT id, nombre FROM estados ORDER BY nombre")
        estados = cursor_db.fetchall()
        cursor_db.execute("SELECT id, nombre FROM disciplinas ORDER BY nombre")
        disciplinas = cursor_db.fetchall()

        txt_matricula = ft.TextField(label="Matrícula *", width=170, autofocus=True)
        txt_apellido_paterno = ft.TextField(label="Apellido Paterno *", width=170)
        txt_apellido_materno = ft.TextField(label="Apellido Materno *", width=170)
        txt_nombres = ft.TextField(label="Nombre(s) *", width=170)
        txt_curp = ft.TextField(label="CURP *", width=200, max_length=18)
        txt_especialidad = ft.TextField(label="Especialidad *", width=200)
        txt_telefono = ft.TextField(label="Teléfono *", width=170, max_length=10)
        txt_ciudad = ft.TextField(label="Ciudad de Origen *", width=170)

        drop_estado = ft.Dropdown(
            label="Estado *", width=190,
            options=[ft.dropdown.Option(str(e[0]), e[1]) for e in estados]
        )

        drop_disciplina = ft.Dropdown(
            label="Disciplina Deportiva", width=200,
            options=[ft.dropdown.Option(str(d[0]), d[1]) for d in disciplinas]
        )

        lbl_resultado = ft.Text("", size=12)
        
        contenedor_tabla = ft.Container(
            content=ft.Column(scroll=ft.ScrollMode.AUTO),
            height=300, bgcolor=ft.Colors.WHITE, border_radius=15, padding=10,
            border=ft.border.all(1, ft.Colors.PURPLE_100),
        )
        
        txt_buscador = ft.TextField(label="Buscar por matrícula o apellido", width=350, prefix_icon=ft.Icons.SEARCH)

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
                    contenedor_tabla.content.controls.append(
                        ft.Container(
                            content=ft.Text("No hay alumnos registrados", color=ft.Colors.GREY_400, size=16),
                            alignment=ft.alignment.center, padding=50,
                        )
                    )
                else:
                    encabezados = ft.Container(
                        content=ft.Row([
                            ft.Text("Matrícula", weight=ft.FontWeight.BOLD, size=13, color=ft.Colors.PURPLE_700, width=100),
                            ft.Text("A. Paterno", weight=ft.FontWeight.BOLD, size=13, color=ft.Colors.PURPLE_700, width=100),
                            ft.Text("A. Materno", weight=ft.FontWeight.BOLD, size=13, color=ft.Colors.PURPLE_700, width=100),
                            ft.Text("Nombre(s)", weight=ft.FontWeight.BOLD, size=13, color=ft.Colors.PURPLE_700, width=100),
                            ft.Text("CURP", weight=ft.FontWeight.BOLD, size=13, color=ft.Colors.PURPLE_700, width=140),
                            ft.Text("Teléfono", weight=ft.FontWeight.BOLD, size=13, color=ft.Colors.PURPLE_700, width=90),
                            ft.Text("Acciones", weight=ft.FontWeight.BOLD, size=13, color=ft.Colors.PURPLE_700, width=100),
                        ], spacing=10),
                        padding=ft.padding.only(bottom=10),
                    )
                    contenedor_tabla.content.controls.append(encabezados)
                    contenedor_tabla.content.controls.append(ft.Divider(color=ft.Colors.PURPLE_100))
                    
                    for alumno in alumnos:
                        def crear_fila(a):
                            def editar_click(e):
                                nonlocal selected_matricula
                                try:
                                    selected_matricula = a[0]
                                    txt_matricula.value = a[0]
                                    txt_matricula.disabled = True
                                    txt_apellido_paterno.value = a[1]
                                    txt_apellido_materno.value = a[2]
                                    txt_nombres.value = a[3]
                                    txt_curp.value = a[4]
                                    txt_telefono.value = a[5]
                                    txt_especialidad.value = a[6]
                                    
                                    drop_estado.value = None
                                    for est in estados:
                                        if est[1] == a[7]:
                                            drop_estado.value = str(est[0])
                                            break
                                    
                                    drop_disciplina.value = None
                                    if a[8] is not None:
                                        for disc in disciplinas:
                                            if disc[1] == a[8]:
                                                drop_disciplina.value = str(disc[0])
                                                break
                                                
                                    lbl_resultado.value = f"Editando: {a[0]}"
                                    lbl_resultado.color = ft.Colors.PURPLE
                                    page.update()
                                except Exception as err:
                                    mostrar_mensaje(f"Error al editar: {str(err)}", ft.Colors.PINK_400)
                            
                            def eliminar_click(e):
                                def confirmar_eliminar(ev):
                                    try:
                                        cursor_db.execute("DELETE FROM alumnos WHERE matricula = %s", (a[0],))
                                        conexion_db.commit()
                                        mostrar_mensaje(f"Alumno {a[0]} eliminado", ft.Colors.PURPLE)
                                        cargar_alumnos(txt_buscador.value)
                                        limpiar_formulario(None)
                                        dialogo.open = False
                                        page.update()
                                    except Exception as ex:
                                        mostrar_mensaje(f"Error: {str(ex)}", ft.Colors.PINK_400)
                                
                                dialogo = ft.AlertDialog(
                                    title=ft.Text("Confirmar eliminación", color=ft.Colors.PURPLE_700),
                                    content=ft.Text(f"¿Eliminar al alumno {a[0]} - {a[3]} {a[1]}?"),
                                    actions=[
                                        ft.TextButton("Cancelar", on_click=lambda _: [setattr(dialogo, "open", False), page.update()]),
                                        ft.ElevatedButton("Eliminar", on_click=confirmar_eliminar, bgcolor=ft.Colors.PINK_400, color=ft.Colors.WHITE),
                                    ],
                                    actions_alignment=ft.MainAxisAlignment.END,
                                )
                                page.dialog = dialogo
                                dialogo.open = True
                                page.update()
                            
                            curp_display = a[4] if a[4] else ""
                            tel_display = a[5] if a[5] else ""
                            
                            return ft.Container(
                                content=ft.Row([
                                    ft.Text(str(a[0]), size=12, width=100),
                                    ft.Text(str(a[1]), size=12, width=100),
                                    ft.Text(str(a[2]), size=12, width=100),
                                    ft.Text(str(a[3]), size=12, width=100),
                                    ft.Text(str(curp_display), size=12, width=140),
                                    ft.Text(str(tel_display), size=12, width=90),
                                    ft.Row([
                                        ft.IconButton(icon=ft.Icons.EDIT, icon_size=18, icon_color=ft.Colors.PURPLE, on_click=editar_click),
                                        ft.IconButton(icon=ft.Icons.DELETE, icon_size=18, icon_color=ft.Colors.PINK_400, on_click=eliminar_click)
                                    ], spacing=0),
                                ], spacing=10, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                                padding=ft.padding.symmetric(vertical=8),
                                border=ft.border.only(bottom=ft.BorderSide(0.5, ft.Colors.PURPLE_50)),
                            )
                        contenedor_tabla.content.controls.append(crear_fila(alumno))
            except Exception as ex:
                mostrar_mensaje(f"Error en Tabla: {str(ex)}", ft.Colors.PINK_400)
            page.update()

        def guardar_alumno(e):
            if not all([txt_matricula.value, txt_apellido_paterno.value, txt_apellido_materno.value, txt_nombres.value, txt_curp.value, txt_especialidad.value, txt_telefono.value, txt_ciudad.value, drop_estado.value]):
                mostrar_mensaje("Complete todos los campos obligatorios", ft.Colors.PINK_400)
                return
            if not validar_curp(txt_curp.value):
                mostrar_mensaje("Formato de CURP inválido", ft.Colors.PINK_400)
                return
            if not validar_telefono(txt_telefono.value):
                mostrar_mensaje("El teléfono debe tener 10 dígitos", ft.Colors.PINK_400)
                return
            try:
                cursor_db.execute("""
                    INSERT INTO alumnos (matricula, apellido_paterno, apellido_materno, nombre,
                        curp, especialidad, telefono, ciudad_origen, estado_id, disciplina_id)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (txt_matricula.value.upper(), txt_apellido_paterno.value.upper(), txt_apellido_materno.value.upper(), txt_nombres.value.upper(), txt_curp.value.upper(), txt_especialidad.value.upper(), txt_telefono.value, txt_ciudad.value.upper(), int(drop_estado.value), int(drop_disciplina.value) if drop_disciplina.value else None))
                conexion_db.commit()
                mostrar_mensaje("Alumno guardado exitosamente", ft.Colors.PURPLE)
                limpiar_formulario(None)
                cargar_alumnos(txt_buscador.value)
            except mysql.connector.IntegrityError as ex:
                if "Duplicate entry" in str(ex):
                    mostrar_mensaje("La matrícula o CURP ya existe", ft.Colors.PINK_400)
                else:
                    mostrar_mensaje(f"Error de integridad: {str(ex)}", ft.Colors.PINK_400)
            except Exception as ex:
                mostrar_mensaje(f"Error: {str(ex)}", ft.Colors.PINK_400)

        def actualizar_alumno(e):
            nonlocal selected_matricula
            if not selected_matricula:
                mostrar_mensaje("Seleccione un alumno para actualizar", ft.Colors.PINK_400)
                return
            try:
                cursor_db.execute("""
                    UPDATE alumnos SET apellido_paterno=%s, apellido_materno=%s, nombre=%s,
                        curp=%s, especialidad=%s, telefono=%s, ciudad_origen=%s, estado_id=%s, disciplina_id=%s
                    WHERE matricula=%s
                """, (txt_apellido_paterno.value.upper(), txt_apellido_materno.value.upper(), txt_nombres.value.upper(), txt_curp.value.upper(), txt_especialidad.value.upper(), txt_telefono.value, txt_ciudad.value.upper(), int(drop_estado.value), int(drop_disciplina.value) if drop_disciplina.value else None, selected_matricula))
                conexion_db.commit()
                mostrar_mensaje("Alumno actualizado exitosamente", ft.Colors.PURPLE)
                limpiar_formulario(None)
                cargar_alumnos(txt_buscador.value)
            except Exception as ex:
                mostrar_mensaje(f"Error: {str(ex)}", ft.Colors.PINK_400)

        txt_buscador.on_change = lambda _: cargar_alumnos(txt_buscador.value)

        def cerrar_sesion(e):
            nonlocal current_user
            current_user = None
            mostrar_login()

        btn_guardar = ft.ElevatedButton("GUARDAR", on_click=guardar_alumno, width=110, height=40, bgcolor=ft.Colors.PURPLE, color=ft.Colors.WHITE)
        btn_actualizar = ft.ElevatedButton("ACTUALIZAR", on_click=actualizar_alumno, width=110, height=40, bgcolor=ft.Colors.PURPLE_300, color=ft.Colors.WHITE)
        btn_limpiar = ft.ElevatedButton("LIMPIAR", on_click=limpiar_formulario, width=110, height=40, bgcolor=ft.Colors.PURPLE_100, color=ft.Colors.PURPLE_700)
        btn_salir = ft.ElevatedButton("SALIR", on_click=cerrar_sesion, width=110, height=40, bgcolor=ft.Colors.PINK_400, color=ft.Colors.WHITE)

        header = ft.Container(
            content=ft.Row([
                ft.Row([
                    ft.Icon(ft.Icons.SCHOOL, size=30, color=ft.Colors.WHITE),
                    ft.Text("Sistema de Gestión de Alumnos", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                ]),
                ft.Row([
                    ft.Text(f"Hola, {current_user}", size=14, color=ft.Colors.WHITE),
                    ft.IconButton(icon=ft.Icons.LOGOUT, icon_color=ft.Colors.WHITE, on_click=cerrar_sesion),
                ]),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            padding=ft.padding.symmetric(horizontal=25, vertical=15),
            bgcolor=ft.Colors.PURPLE,
            border_radius=ft.border_radius.only(bottom_left=20, bottom_right=20),
        )

        form_card = ft.Container(
            content=ft.Column([
                ft.Text("REGISTRO DE ALUMNOS", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.PURPLE_700),
                ft.Divider(color=ft.Colors.PURPLE_100),
                ft.Row([txt_matricula, txt_apellido_paterno, txt_apellido_materno], wrap=True, spacing=15),
                ft.Row([txt_nombres, txt_curp, txt_especialidad], wrap=True, spacing=15),
                ft.Row([txt_telefono, txt_ciudad, drop_estado], wrap=True, spacing=15),
                ft.Row([drop_disciplina], wrap=True, spacing=15),
                ft.Row([btn_guardar, btn_actualizar, btn_limpiar, btn_salir], alignment=ft.MainAxisAlignment.CENTER, spacing=20),
                lbl_resultado,
            ], spacing=15, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            padding=20, bgcolor=ft.Colors.WHITE, border_radius=20, margin=ft.margin.all(10),
        )

        search_bar = ft.Container(
            content=ft.Row([txt_buscador], alignment=ft.MainAxisAlignment.END),
            padding=ft.padding.only(right=10, bottom=10),
        )

        page.add(
            ft.Column([
                header,
                ft.Container(
                    content=ft.Column([form_card, search_bar, contenedor_tabla], spacing=10),
                    expand=True, padding=20,
                )
            ], spacing=0, expand=True)
        )
        
        cargar_alumnos("")
        page.update()

    mostrar_login()

if __name__ == "__main__":
    ft.app(target=main)