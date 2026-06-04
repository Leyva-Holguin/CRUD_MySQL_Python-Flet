-- Crear base de datos
CREATE DATABASE IF NOT EXISTS sistema_alumnos;
USE sistema_alumnos;

-- Tabla de usuarios
CREATE TABLE IF NOT EXISTS usuarios (
    id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL
);

-- Tabla de alumnos
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
);

-- Insertar usuario admin (contraseña: admin123)
INSERT INTO usuarios (username, password_hash) 
VALUES ('admin', '$2b$12$...'); -- Aquí va el hash generado con bcrypt

-- Datos de prueba
INSERT INTO alumnos VALUES 
('A001', 'GARCIA', 'LOPEZ', 'JUAN', 'GALJ010101HDFLPR01', 'INGENIERIA', '5551234567', 'CDMX', 'CIUDAD DE MÉXICO', 'FÚTBOL', NULL);