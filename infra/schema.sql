-- Run this after RDS is available.
-- From WSL: psql -h <DB_HOST> -U salesadmin -d salesdb -f infra/schema.sql

CREATE TYPE tipo_direccion_enum AS ENUM ('FACTURACIÓN', 'ENVÍO');

CREATE TABLE clients (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    razon_social VARCHAR(255) NOT NULL,
    nombre_comercial VARCHAR(255) NOT NULL,
    rfc VARCHAR(13) NOT NULL UNIQUE,
    correo_electronico VARCHAR(255) NOT NULL,
    telefono VARCHAR(20) NOT NULL
);

CREATE TABLE addresses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    domicilio VARCHAR(255) NOT NULL,
    colonia VARCHAR(255) NOT NULL,
    municipio VARCHAR(255) NOT NULL,
    estado VARCHAR(255) NOT NULL,
    tipo_direccion tipo_direccion_enum NOT NULL
);

CREATE TABLE products (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nombre VARCHAR(255) NOT NULL,
    unidad_medida VARCHAR(50) NOT NULL,
    precio_base NUMERIC(12,2) NOT NULL
);

CREATE TABLE sell_notes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    folio VARCHAR(50) NOT NULL UNIQUE,
    client_id UUID NOT NULL REFERENCES clients(id) ON DELETE RESTRICT,
    direccion_facturacion_id UUID NOT NULL REFERENCES addresses(id) ON DELETE RESTRICT,
    direccion_envio_id UUID NOT NULL REFERENCES addresses(id) ON DELETE RESTRICT,
    total NUMERIC(12,2) NOT NULL,
    pdf_s3_key VARCHAR(512)
);

CREATE TABLE sell_note_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sell_note_id UUID NOT NULL REFERENCES sell_notes(id) ON DELETE CASCADE,
    product_id UUID NOT NULL REFERENCES products(id) ON DELETE RESTRICT,
    cantidad NUMERIC(10,3) NOT NULL,
    precio_unitario NUMERIC(12,2) NOT NULL,
    importe NUMERIC(12,2) NOT NULL
);
