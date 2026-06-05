CREATE DATABASE IF NOT EXISTS sistema_alumnos;
USE sistema_alumnos;

CREATE TABLE usuarios (
    id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL
);

CREATE TABLE alumnos (
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
);

INSERT INTO alumnos (
    matricula,
    apellido_paterno,
    apellido_materno,
    nombre,
    curp,
    especialidad,
    telefono,
    ciudad_origen,
    estado,
    disciplina,
    foto_url
)
VALUES
(
    'A2024001',
    'GARCIA',
    'LOPEZ',
    'JUAN CARLOS',
    'GALJ010101HDFRRN01',
    'INGENIERIA EN SISTEMAS',
    '5551234567',
    'GUADALAJARA',
    'JALISCO',
    'FUTBOL',
    'https://randomuser.me/api/portraits/men/1.jpg'
),
(
    'A2024006',
    'PEREZ',
    'DIAZ',
    'VALENTINA',
    'PEDV060606MDFRRN06',
    'PSICOLOGIA',
    '5556789012',
    'TOLUCA',
    'ESTADO DE MEXICO',
    'GIMNASIA',
    'https://randomuser.me/api/portraits/women/6.jpg'
),
(
    'A2024007',
    'GONZALEZ',
    'TORRES',
    'DIEGO',
    'GOTD070707HDFRRN07',
    'DERECHO',
    '5557890123',
    'LEON',
    'GUANAJUATO',
    'AJEDREZ',
    'https://randomuser.me/api/portraits/men/7.jpg'
);

INSERT INTO usuarios (username, password_hash)
VALUES (
    'admin',
    '$2b$12$KIXqUiZEbL.n3sK6Z.7OcOj5n5K7Y8x9z0a1b2c3d4e5f6g7h8i9j0'
);

