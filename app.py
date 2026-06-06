import flet as ft
import mysql.connector
import bcrypt
import re
import sys

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
    
    current_user = None
    selected_matricula = None
    SHADOW_COLOR = "#1A000000"
    
    conexion = None
    cursor = None
    
    def conectar_bd():
        nonlocal conexion, cursor
        try:
            if conexion is None or not conexion.is_connected():
                conexion = mysql.connector.connect(
                    host='localhost',
                    user='root',
                    password='admin123',
                    database='sistema_alumnos'
                )
                cursor = conexion.cursor()
            return conexion
        except Exception as e:
            print(f"Error de conexión: {e}")
            return None
    
    def ejecutar_query(query, params=None):
        nonlocal conexion, cursor
        try:
            if conectar_bd() is None:
                return None
            cursor.execute(query, params or ())
            if query.strip().upper().startswith('SELECT'):
                return cursor.fetchall()
            else:
                conexion.commit()
                return cursor.rowcount
        except Exception as e:
            print(f"Error en consulta: {e}")
            if conexion:
                conexion.rollback()
            return None
    
    try:
        temp_conn = mysql.connector.connect(
            host='localhost', user='root', password='admin123'
        )
        temp_cursor = temp_conn.cursor()
        temp_cursor.execute("CREATE DATABASE IF NOT EXISTS sistema_alumnos")
        temp_cursor.close()
        temp_conn.close()
        
        conectar_bd()
        
        ejecutar_query("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id INT PRIMARY KEY AUTO_INCREMENT,
                username VARCHAR(50) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL
            )
        """)
        ejecutar_query("""
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
                foto_url VARCHAR(500)
            )
        """)
        
        resultado = ejecutar_query("SELECT COUNT(*) FROM usuarios")
        if resultado and resultado[0][0] == 0:
            salt = bcrypt.gensalt()
            ph = bcrypt.hashpw("admin123".encode(), salt)
            ejecutar_query(
                "INSERT INTO usuarios (username, password_hash) VALUES (%s, %s)",
                ("admin", ph)
            )
        print("Base de datos inicializada correctamente")
    except Exception as e:
        print(f"Error inicializando BD: {e}")
        return
    
    def mostrar_mensaje(texto, color):
        snack = ft.SnackBar(
            content=ft.Text(texto, color=ft.Colors.WHITE),
            bgcolor=color, duration=3000, open=True
        )
        page.overlay.append(snack)
        snack.open = True
        page.update()
    
    def validar_curp(curp):
        curp = curp.upper().strip()
        patron = r'^[A-Z][AEIOU][A-Z]{2}\d{6}[A-Z]{6}\d{2}$'
        patron_alternativo = r'^[A-ZÑ][AEIOUX][A-ZÑ]{2}\d{6}[A-ZÑ]{6}\d{2}$'
        
        if re.match(patron, curp) or re.match(patron_alternativo, curp):
            try:
                anno = int(curp[4:6])
                mes = int(curp[6:8])
                dia = int(curp[8:10])
                if anno < 0 or anno > 99 or mes < 1 or mes > 12 or dia < 1 or dia > 31:
                    return False
                return True
            except:
                return False
        return False
    
    def validar_matricula(matricula):
        matricula = matricula.strip()
        if not matricula:
            return False
        if not matricula.isdigit():
            return False
        if len(matricula) < 1 or len(matricula) > 14:
            return False
        return True
    
    def validar_telefono(tel):
        return bool(re.match(r'^\d{10}$', tel))
    
    def validar_url_imagen(url):
        if not url or url.strip() == "":
            return True
        extensiones_validas = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']
        return any(url.lower().endswith(ext) for ext in extensiones_validas)
    
    especialidades = [
        "Programación",
        "Administración de Recursos Humanos",
        "Secretariado Ejecutivo Bilingüe",
        "Electrónica"
    ]
    
    disciplinas = [
        "FUTBOL", "BASQUETBOL", "VOLEIBOL", "ATLETISMO", "NATACION",
        "TENIS", "BOXEO", "TAEKWONDO", "JUDO", "GIMNASIA", "CICLISMO",
        "AJEDREZ", "NINGUNA"
    ]
    
    estados_mexico = [
        "AGUASCALIENTES", "BAJA CALIFORNIA", "BAJA CALIFORNIA SUR", "CAMPECHE",
        "CHIAPAS", "CHIHUAHUA", "CIUDAD DE MEXICO", "COAHUILA", "COLIMA",
        "DURANGO", "ESTADO DE MEXICO", "GUANAJUATO", "GUERRERO", "HIDALGO",
        "JALISCO", "MICHOACAN", "MORELOS", "NAYARIT", "NUEVO LEON", "OAXACA",
        "PUEBLA", "QUERETARO", "QUINTANA ROO", "SAN LUIS POTOSI", "SINALOA",
        "SONORA", "TABASCO", "TAMAULIPAS", "TLAXCALA", "VERACRUZ", "YUCATAN", "ZACATECAS"
    ]
    
    def mostrar_login():
        nonlocal current_user
        current_user = None
        
        txt_usuario = ft.TextField(
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
                page.update()
                return
            try:
                resultado = ejecutar_query(
                    "SELECT password_hash FROM usuarios WHERE username=%s", (u,)
                )
                if resultado:
                    bh = resultado[0][0]
                    if not isinstance(bh, bytes):
                        bh = bh.encode()
                    if bcrypt.checkpw(p.encode(), bh):
                        current_user = u
                        mostrar_panel()
                        return
                lbl_error.value = "Usuario o contraseña incorrectos"
                page.update()
            except Exception as ex:
                lbl_error.value = f"Error: {ex}"
                page.update()
        
        def ir_registro(e):
            mostrar_registro()
        
        card = ft.Container(
            content=ft.Column([
                ft.Icon(ft.Icons.SCHOOL, size=70, color=ft.Colors.PURPLE),
                ft.Text("SISTEMA DE GESTION", size=24,
                        weight=ft.FontWeight.BOLD, color=ft.Colors.PURPLE_700),
                ft.Text("DE ALUMNOS", size=20,
                        weight=ft.FontWeight.W_500, color=ft.Colors.PURPLE_400),
                ft.Divider(height=20, color=ft.Colors.PURPLE_100),
                txt_usuario, txt_password, lbl_error,
                ft.ElevatedButton("INGRESAR", on_click=iniciar_sesion,
                                  width=320, height=45,
                                  bgcolor=ft.Colors.PURPLE, color=ft.Colors.WHITE),
                ft.TextButton("Crear cuenta nueva", on_click=ir_registro),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=15),
            width=420, padding=40,
            bgcolor=ft.Colors.WHITE, border_radius=30,
            shadow=ft.BoxShadow(blur_radius=15, color=SHADOW_COLOR)
        )
        
        page.controls.clear()
        page.add(ft.Column([card], horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                          alignment=ft.MainAxisAlignment.CENTER, expand=True))
        page.window.width = 480
        page.window.height = 640
        page.update()
    
    def mostrar_registro():
        txt_u = ft.TextField(label="Nuevo Usuario", width=320,
                             prefix_icon=ft.Icons.PERSON, autofocus=True,
                             border_color=ft.Colors.PURPLE_200,
                             focused_border_color=ft.Colors.PURPLE)
        txt_p = ft.TextField(label="Contraseña", width=320,
                             password=True, can_reveal_password=True,
                             prefix_icon=ft.Icons.LOCK,
                             border_color=ft.Colors.PURPLE_200,
                             focused_border_color=ft.Colors.PURPLE)
        txt_c = ft.TextField(label="Confirmar Contraseña", width=320,
                             password=True, can_reveal_password=True,
                             prefix_icon=ft.Icons.LOCK,
                             border_color=ft.Colors.PURPLE_200,
                             focused_border_color=ft.Colors.PURPLE)
        lbl_err = ft.Text("", color=ft.Colors.PINK_400, size=12)
        
        def registrar(e):
            u, p, c = txt_u.value.strip(), txt_p.value, txt_c.value
            if not u or not p:
                lbl_err.value = "Complete todos los campos"
                page.update()
                return
            if p != c:
                lbl_err.value = "Las contraseñas no coinciden"
                page.update()
                return
            try:
                salt = bcrypt.gensalt()
                ph = bcrypt.hashpw(p.encode(), salt)
                ejecutar_query(
                    "INSERT INTO usuarios (username, password_hash) VALUES (%s,%s)",
                    (u, ph)
                )
                mostrar_mensaje(f"Usuario '{u}' creado", ft.Colors.PURPLE)
                mostrar_login()
            except Exception as ex:
                if "Duplicate" in str(ex):
                    lbl_err.value = "El usuario ya existe"
                else:
                    lbl_err.value = f"Error: {ex}"
                page.update()
        
        def volver_login(e):
            mostrar_login()
        
        card = ft.Container(
            content=ft.Column([
                ft.Icon(ft.Icons.SCHOOL, size=60, color=ft.Colors.PURPLE),
                ft.Text("CREAR NUEVA CUENTA", size=24,
                        weight=ft.FontWeight.BOLD, color=ft.Colors.PURPLE_700),
                ft.Divider(height=20, color=ft.Colors.PURPLE_100),
                txt_u, txt_p, txt_c, lbl_err,
                ft.ElevatedButton("Registrar", on_click=registrar,
                                  width=320, height=45,
                                  bgcolor=ft.Colors.PURPLE, color=ft.Colors.WHITE),
                ft.TextButton("Volver al Login", on_click=volver_login),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=15),
            width=420, padding=40,
            bgcolor=ft.Colors.WHITE, border_radius=30,
            shadow=ft.BoxShadow(blur_radius=15, color=SHADOW_COLOR)
        )
        
        page.controls.clear()
        page.add(ft.Column([card], horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                          alignment=ft.MainAxisAlignment.CENTER, expand=True))
        page.window.width = 480
        page.window.height = 680
        page.update()
    
    def mostrar_panel():
        nonlocal selected_matricula
        selected_matricula = None
        
        filtro_solo_numeros = ft.InputFilter(allow=True, regex_string=r"[0-9]", replacement_string="")
        filtro_letras = ft.InputFilter(allow=True, regex_string=r"[a-zA-ZáéíóúÁÉÍÓÚñÑ ]", replacement_string="")
        
        txt_matricula = ft.TextField(
            label="Matrícula *", 
            width=220,
            input_filter=filtro_solo_numeros,
            max_length=14,
            hint_text="Solo números"
        )
        txt_apellido_paterno = ft.TextField(label="Apellido Paterno *", input_filter=filtro_letras, width=220)
        txt_apellido_materno = ft.TextField(label="Apellido Materno *", input_filter=filtro_letras, width=220)
        txt_nombres = ft.TextField(label="Nombre(s) *", input_filter=filtro_letras, width=220)
        txt_curp = ft.TextField(
            label="CURP *", 
            max_length=18, 
            width=220, 
            capitalization=ft.TextCapitalization.CHARACTERS,
            hint_text="Ej: GODE561231HDFRRN09"
        )
        
        txt_especialidad = ft.Dropdown(
            label="Especialidad *", 
            width=220,
            options=[ft.dropdown.Option(esp) for esp in especialidades]
        )
        
        txt_telefono = ft.TextField(label="Teléfono *", max_length=10, input_filter=filtro_solo_numeros, width=220)
        txt_ciudad = ft.TextField(label="Ciudad de Origen *", input_filter=filtro_letras, width=220)
        txt_foto_url = ft.TextField(label="URL de la foto", width=220, prefix_icon=ft.Icons.LINK,
                                    hint_text="https://ejemplo.com/foto.jpg")
        
        txt_estado = ft.Dropdown(label="Estado *", width=220, 
                                  options=[ft.dropdown.Option(estado) for estado in estados_mexico])
        
        txt_disciplina = ft.Dropdown(label="Disciplina Deportiva", width=220,
                                      options=[ft.dropdown.Option(disciplina) for disciplina in disciplinas])
        
        IMG_DEFECTO = "https://cdn-icons-png.flaticon.com/512/3135/3135715.png"
        img_perfil = ft.Image(src=IMG_DEFECTO, width=110, height=110, fit="cover", border_radius=55)
        lbl_resultado = ft.Text("", size=12, color=ft.Colors.PURPLE_400)
        
        contenedor_tabla = ft.Container(
            content=ft.Column(scroll=ft.ScrollMode.AUTO),
            height=280,
            bgcolor=ft.Colors.WHITE,
            border_radius=15,
            padding=20,
            border=ft.Border.all(1, ft.Colors.PURPLE_100),
        )
        txt_buscador = ft.TextField(label="Buscar por matrícula o apellido", width=350, prefix_icon=ft.Icons.SEARCH)
        
        def actualizar_vista_previa(e):
            if txt_foto_url.value and txt_foto_url.value.strip():
                if validar_url_imagen(txt_foto_url.value):
                    img_perfil.src = txt_foto_url.value.strip()
                else:
                    img_perfil.src = IMG_DEFECTO
                    mostrar_mensaje("Formato de imagen no válido (use .jpg, .png, .gif, etc.)", ft.Colors.PINK_400)
            else:
                img_perfil.src = IMG_DEFECTO
            img_perfil.update()
        
        txt_foto_url.on_change = actualizar_vista_previa
        
        def limpiar():
            nonlocal selected_matricula
            txt_matricula.value = ""
            txt_apellido_paterno.value = ""
            txt_apellido_materno.value = ""
            txt_nombres.value = ""
            txt_curp.value = ""
            txt_especialidad.value = None
            txt_telefono.value = ""
            txt_ciudad.value = ""
            txt_foto_url.value = ""
            txt_estado.value = None
            txt_disciplina.value = None
            txt_matricula.disabled = False
            selected_matricula = None
            img_perfil.src = IMG_DEFECTO
            lbl_resultado.value = ""
            page.update()
        
        def cargar_alumnos(busqueda=""):
            contenedor_tabla.content.controls.clear()
            try:
                if busqueda:
                    alumnos = ejecutar_query("""
                        SELECT matricula, apellido_paterno, apellido_materno,
                               nombre, curp, telefono, especialidad,
                               estado, disciplina, foto_url, ciudad_origen
                        FROM alumnos
                        WHERE matricula LIKE %s OR apellido_paterno LIKE %s
                        ORDER BY matricula
                    """, (f"%{busqueda}%", f"%{busqueda}%"))
                else:
                    alumnos = ejecutar_query("""
                        SELECT matricula, apellido_paterno, apellido_materno,
                               nombre, curp, telefono, especialidad,
                               estado, disciplina, foto_url, ciudad_origen
                        FROM alumnos ORDER BY matricula
                    """)
                
                if not alumnos:
                    contenedor_tabla.content.controls.append(
                        ft.Container(
                            content=ft.Text("No hay alumnos registrados", color=ft.Colors.GREY_500, size=14),
                            alignment=ft.Alignment(0, 0), padding=40
                        )
                    )
                else:
                    contenedor_tabla.content.controls.append(
                        ft.Container(
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
                            padding=10
                        )
                    )
                    contenedor_tabla.content.controls.append(ft.Divider(color=ft.Colors.PURPLE_100, height=1))
                    
                    for reg in alumnos:
                        def crear_fila(a):
                            def editar(e):
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
                                txt_estado.value = a[7]
                                txt_disciplina.value = a[8] if a[8] else "NINGUNA"
                                txt_foto_url.value = a[9] if a[9] else ""
                                txt_ciudad.value = a[10]
                                img_perfil.src = a[9] if a[9] else IMG_DEFECTO
                                lbl_resultado.value = f"Editando: {a[0]}"
                                page.update()
                            
                            def eliminar(e):
                                def cerrar():
                                    dialogo.open = False
                                    page.update()
                                
                                def confirmar():
                                    try:
                                        ejecutar_query("DELETE FROM alumnos WHERE matricula=%s", (a[0],))
                                        mostrar_mensaje("Registro eliminado", ft.Colors.PINK_400)
                                        cargar_alumnos(txt_buscador.value)
                                        limpiar()
                                    except Exception as ex:
                                        print(f"Error al eliminar: {ex}")
                                    dialogo.open = False
                                    page.update()
                                
                                dialogo = ft.AlertDialog(
                                    modal=True,
                                    title=ft.Text("Confirmar eliminación"),
                                    content=ft.Text(f"¿Eliminar permanentemente al alumno {a[0]}?"),
                                    actions=[
                                        ft.TextButton("Cancelar", on_click=lambda _: cerrar()),
                                        ft.ElevatedButton("Eliminar", on_click=lambda _: confirmar(),
                                                         bgcolor=ft.Colors.PINK_400, color=ft.Colors.WHITE),
                                    ],
                                )
                                page.overlay.append(dialogo)
                                dialogo.open = True
                                page.update()
                            
                            foto_src = a[9] if a[9] else IMG_DEFECTO
                            mini_foto = ft.Image(src=foto_src, width=30, height=30, fit="cover", border_radius=15)
                            return ft.Container(
                                content=ft.Row([
                                    ft.Container(content=mini_foto, width=60, alignment=ft.Alignment(-1, 0)),
                                    ft.Text(str(a[0]), size=12, width=100),
                                    ft.Text(str(a[1]), size=12, width=110),
                                    ft.Text(str(a[2]), size=12, width=110),
                                    ft.Text(str(a[3]), size=12, width=130),
                                    ft.Text(str(a[4]), size=12, width=150),
                                    ft.Text(str(a[5]), size=12, width=90),
                                    ft.Row([
                                        ft.IconButton(icon=ft.Icons.EDIT, icon_size=18, icon_color=ft.Colors.PURPLE, on_click=editar),
                                        ft.IconButton(icon=ft.Icons.DELETE, icon_size=18, icon_color=ft.Colors.PINK_400, on_click=eliminar),
                                    ], spacing=0),
                                ], spacing=10),
                                padding=5,
                            )
                        contenedor_tabla.content.controls.append(crear_fila(reg))
                page.update()
            except Exception as ex:
                print(f"Error al cargar lista: {ex}")
        
        def guardar(e):
            if txt_matricula.disabled:
                mostrar_mensaje("Use Actualizar para modificar un alumno existente", ft.Colors.ORANGE)
                return
            
            if not validar_matricula(txt_matricula.value):
                mostrar_mensaje("Matrícula inválida: debe contener solo números y tener entre 1 y 14 dígitos", ft.Colors.PINK_400)
                return
                
            if not all([txt_matricula.value, txt_apellido_paterno.value, txt_apellido_materno.value,
                        txt_nombres.value, txt_curp.value, txt_especialidad.value,
                        txt_telefono.value, txt_ciudad.value, txt_estado.value]):
                mostrar_mensaje("Complete todos los campos obligatorios (*)", ft.Colors.PINK_400)
                return
            
            if not validar_curp(txt_curp.value):
                mostrar_mensaje("CURP inválida. Formato: 4 letras + 6 números (fecha) + 6 letras + 2 dígitos", ft.Colors.PINK_400)
                return
                
            if not validar_telefono(txt_telefono.value):
                mostrar_mensaje("Teléfono debe tener 10 dígitos", ft.Colors.PINK_400)
                return
            if txt_foto_url.value and not validar_url_imagen(txt_foto_url.value):
                mostrar_mensaje("URL de imagen inválida (use .jpg, .png, .gif, etc.)", ft.Colors.PINK_400)
                return
            
            try:
                ejecutar_query("""
                    INSERT INTO alumnos (matricula, apellido_paterno, apellido_materno,
                        nombre, curp, especialidad, telefono, ciudad_origen,
                        estado, disciplina, foto_url)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """, (
                    txt_matricula.value.upper(),
                    txt_apellido_paterno.value.upper(),
                    txt_apellido_materno.value.upper(),
                    txt_nombres.value.upper(),
                    txt_curp.value.upper(),
                    txt_especialidad.value,
                    txt_telefono.value,
                    txt_ciudad.value.upper(),
                    txt_estado.value,
                    txt_disciplina.value if txt_disciplina.value else None,
                    txt_foto_url.value if txt_foto_url.value else None
                ))
                mostrar_mensaje("Alumno registrado correctamente", ft.Colors.PURPLE)
                limpiar()
                cargar_alumnos(txt_buscador.value)
            except Exception as ex:
                if "Duplicate" in str(ex):
                    if "curp" in str(ex).lower():
                        mostrar_mensaje("Error: Esta CURP ya está registrada", ft.Colors.PINK_400)
                    else:
                        mostrar_mensaje("Error: Matrícula ya existe", ft.Colors.PINK_400)
                else:
                    mostrar_mensaje(f"Error al guardar: {ex}", ft.Colors.PINK_400)
        
        def actualizar(e):
            nonlocal selected_matricula
            if not selected_matricula:
                mostrar_mensaje("Selecciona un alumno de la tabla primero", ft.Colors.PINK_400)
                return
            if not all([txt_apellido_paterno.value, txt_apellido_materno.value, txt_nombres.value,
                        txt_curp.value, txt_especialidad.value, txt_telefono.value,
                        txt_ciudad.value, txt_estado.value]):
                mostrar_mensaje("Complete todos los campos obligatorios (*)", ft.Colors.PINK_400)
                return
            
            if not validar_curp(txt_curp.value):
                mostrar_mensaje("CURP inválida. Formato: 4 letras + 6 números (fecha) + 6 letras + 2 dígitos", ft.Colors.PINK_400)
                return
                
            if not validar_telefono(txt_telefono.value):
                mostrar_mensaje("Teléfono debe tener 10 dígitos", ft.Colors.PINK_400)
                return
            if txt_foto_url.value and not validar_url_imagen(txt_foto_url.value):
                mostrar_mensaje("URL de imagen inválida (use .jpg, .png, .gif, etc.)", ft.Colors.PINK_400)
                return
            
            try:
                ejecutar_query("""
                    UPDATE alumnos SET
                        apellido_paterno=%s, apellido_materno=%s,
                        nombre=%s, curp=%s, especialidad=%s,
                        telefono=%s, ciudad_origen=%s, estado=%s,
                        disciplina=%s, foto_url=%s
                    WHERE matricula=%s
                """, (
                    txt_apellido_paterno.value.upper(),
                    txt_apellido_materno.value.upper(),
                    txt_nombres.value.upper(),
                    txt_curp.value.upper(),
                    txt_especialidad.value,
                    txt_telefono.value,
                    txt_ciudad.value.upper(),
                    txt_estado.value,
                    txt_disciplina.value if txt_disciplina.value else None,
                    txt_foto_url.value if txt_foto_url.value else None,
                    selected_matricula
                ))
                mostrar_mensaje("Alumno actualizado correctamente", ft.Colors.PURPLE)
                limpiar()
                cargar_alumnos(txt_buscador.value)
            except Exception as ex:
                if "Duplicate" in str(ex) and "curp" in str(ex).lower():
                    mostrar_mensaje("Error: Esta CURP ya está registrada por otro alumno", ft.Colors.PINK_400)
                else:
                    mostrar_mensaje(f"Error al actualizar: {ex}", ft.Colors.PINK_400)
        
        def salir(e):
            nonlocal conexion, cursor
            try:
                if cursor:
                    cursor.close()
                if conexion and conexion.is_connected():
                    conexion.close()
            except:
                pass
            sys.exit(0)
        
        txt_buscador.on_change = lambda _: cargar_alumnos(txt_buscador.value)
        
        header = ft.Container(
            content=ft.Row([
                ft.Row([
                    ft.Icon(ft.Icons.SCHOOL, color=ft.Colors.WHITE),
                    ft.Text("Sistema de Gestión de Alumnos", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                ]),
                ft.Row([
                    ft.Text(f"Usuario: {current_user}", size=13, color=ft.Colors.PURPLE_100),
                    ft.IconButton(icon=ft.Icons.LOGOUT, icon_color=ft.Colors.WHITE, tooltip="Cerrar sesión", on_click=lambda _: mostrar_login()),
                ])
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
                    ft.Row([txt_disciplina, txt_foto_url], spacing=15),
                    ft.Divider(height=5, color=ft.Colors.TRANSPARENT),
                    ft.Row([
                        ft.ElevatedButton("Guardar", on_click=guardar, width=130, bgcolor=ft.Colors.PURPLE, color=ft.Colors.WHITE),
                        ft.ElevatedButton("Actualizar", on_click=actualizar, width=130, bgcolor=ft.Colors.PURPLE_300, color=ft.Colors.WHITE),
                        ft.ElevatedButton("Limpiar", on_click=lambda _: limpiar(), width=130, bgcolor=ft.Colors.PURPLE_100, color=ft.Colors.PURPLE_700),
                        ft.ElevatedButton("Salir", on_click=salir, width=130, bgcolor=ft.Colors.PINK_400, color=ft.Colors.WHITE),
                    ], spacing=10),
                    lbl_resultado,
                ], spacing=12, expand=True),
                ft.VerticalDivider(width=20, color=ft.Colors.PURPLE_50),
                ft.Column([
                    ft.Text("FOTO PERFIL", size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.PURPLE_700),
                    ft.Container(content=img_perfil, border=ft.Border.all(2, ft.Colors.PURPLE_200), border_radius=60, padding=4),
                    ft.Text("Ingresa la URL de la imagen", size=10, color=ft.Colors.GREY_500),
                    ft.Text("Formatos: .jpg, .png, .gif", size=9, color=ft.Colors.GREY_400),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10, width=200),
            ]),
            padding=25, bgcolor=ft.Colors.WHITE, border_radius=20, shadow=ft.BoxShadow(blur_radius=10, color=SHADOW_COLOR)
        )
        
        panel = ft.Container(
            content=ft.Column([
                header,
                form_card,
                ft.Container(content=ft.Row([txt_buscador], alignment=ft.MainAxisAlignment.END), padding=5),
                contenedor_tabla,
            ], spacing=15),
            padding=ft.Padding(left=20, right=20, top=15, bottom=15)
        )
        
        page.controls.clear()
        page.add(ft.Row([panel], expand=True))
        page.window.width = 1350
        page.window.height = 850
        page.horizontal_alignment = ft.CrossAxisAlignment.START
        page.vertical_alignment = ft.MainAxisAlignment.START
        page.scroll = ft.ScrollMode.AUTO
        page.update()
        cargar_alumnos()
    
    mostrar_login()

ft.run(main)