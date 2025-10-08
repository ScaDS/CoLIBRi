CREATE USER cpt_db_user WITH ENCRYPTED PASSWORD 'SCRAM-SHA-256$4096:zWf3siLwItDqYkWHawZNeQ==$oqXFDgsYmtCs+4zzymxb8jCyoOszjChGfjIa3B/rH4M=:wABoXahd6SPk/doIJnOj70YD8o0gBk68z5UMuMJ946w=';
CREATE DATABASE cpt_db;
GRANT ALL PRIVILEGES ON DATABASE cpt_db TO cpt_db_user;
\c cpt_db db_admin
GRANT ALL ON SCHEMA public TO cpt_db_user;
GRANT pg_read_server_files TO cpt_db_user;
\c cpt_db cpt_db_user

CREATE TEMP TABLE drawings_staging (
    drawing_id INTEGER PRIMARY KEY,
    original_drawing TEXT
);
CREATE TABLE IF NOT EXISTS drawings (
    drawing_id INTEGER PRIMARY KEY,
    original_drawing BYTEA
);
CREATE TABLE IF NOT EXISTS runtimes (
    runtime_id SERIAL PRIMARY KEY,
    drawing_id INTEGER references drawings(drawing_id) ON DELETE CASCADE,
    machine TEXT NOT NULL,
    machine_runtime FLOAT NOT NULL
);
CREATE TABLE IF NOT EXISTS searchdata (
    searchdata_id INTEGER PRIMARY KEY,
    drawing_id INTEGER references drawings(drawing_id) ON DELETE CASCADE,
    shape FLOAT[],
    material TEXT[],
    general_tolerances TEXT[],
    surfaces TEXT[],
    gdts TEXT[],
    threads TEXT[],
    outer_dimensions FLOAT[],
    search_vector FLOAT[],
    part_number TEXT,
    ocr_text TEXT[],
    runtime_text TEXT,
    llm_text TEXT,
    llm_vector FLOAT []
);
CREATE TABLE IF NOT EXISTS history (
    history_id SERIAL PRIMARY KEY,
    query_drawing BYTEA,
    query_path TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS feedbacks (
    feedback_id SERIAL PRIMARY KEY,
    history_id INTEGER references history(history_id) ON DELETE RESTRICT,
    drawing_id INTEGER references drawings(drawing_id) ON DELETE RESTRICT,
    feedback_desc TEXT,
    feedback_value INTEGER
);

COPY drawings_staging(drawing_id, original_drawing)
FROM '/var/lib/postgresql/resources/example_data/drawings.csv'
DELIMITER ','
CSV HEADER;
INSERT INTO drawings (drawing_id, original_drawing)
SELECT drawing_id, decode(original_drawing, 'base64')
FROM drawings_staging;

COPY runtimes(runtime_id, drawing_id, machine, machine_runtime)
FROM '/var/lib/postgresql/resources/example_data/runtimes.csv'
DELIMITER ','
CSV HEADER;

COPY searchdata(searchdata_id, drawing_id, shape, material, general_tolerances, surfaces, gdts, threads, outer_dimensions, search_vector, part_number, ocr_text, runtime_text, llm_text, llm_vector)
FROM '/var/lib/postgresql/resources/example_data/searchdata.csv'
DELIMITER ','
CSV HEADER;