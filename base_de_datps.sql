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
    foto_url VARCHAR(500)
);

-- Usuario de prueba (contraseña: admin123)
INSERT INTO usuarios (username, password_hash) VALUES 
('admin', '$2b$12$ejemplo...');

-- Alumnos de prueba
INSERT INTO alumnos (matricula, apellido_paterno, apellido_materno, nombre, curp, especialidad, telefono, ciudad_origen, estado, disciplina, foto_url) VALUES
('A2024001', 'GARCIA', 'LOPEZ', 'JUAN', 'GALJ880101HDFRRN09', 'INFORMATICA', '5551234567', 'CHIHUAHUA', 'CHIHUAHUA', 'FUTBOL', 'https://randomuser.me/api/portraits/men/1.jpg'),
('A2024002', 'MARTINEZ', 'RODRIGUEZ', 'MARIA', 'MARF950215HDFRRN08', 'CONTABILIDAD', '5558765432', 'MONTERREY', 'NUEVO LEON', 'BASQUETBOL', 'https://randomuser.me/api/portraits/women/1.jpg');