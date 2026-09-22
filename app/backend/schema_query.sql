DROP TABLE IF EXISTS audit_logs, tickets, requesters, severities, departments, users CASCADE;

CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) NOT NULL UNIQUE,
    pw_hash VARCHAR(255) NOT NULL
);

CREATE TABLE departments (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE
);

CREATE TABLE severities (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    respond_time_hours INT NOT NULL,
    resolve_time_hours INT NOT NULL
);

CREATE TABLE requesters (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    name VARCHAR(100)
);

CREATE TABLE tickets (
    id SERIAL PRIMARY KEY,
    requestor_id INT REFERENCES requesters(id) NOT NULL,
    email_subject VARCHAR(255),
    email_body TEXT,
    assigned_team_id INT REFERENCES departments(id) NOT NULL,
    sev_id INT REFERENCES severities(id) NOT NULL,
    ai_explaination TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    resolved_at TIMESTAMP
);

CREATE TABLE audit_logs (
    id SERIAL PRIMARY KEY,
    ticket_id INT REFERENCES tickets(id) NOT NULL,
    action VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    created_by INT REFERENCES users(id) NOT NULL
);

INSERT INTO departments (name) 
VALUES
  ('IT'),
  ('Engineering'),
  ('Finance'),
  ('Legal & Compliance'),
  ('HR'),
  ('Info Security'),
  ('Client Success'),
  ('Facilities');

INSERT INTO severities (name, respond_time_hours, resolve_time_hours)
VALUES
  ('High', 8, 24),
  ('Med', 24, 72),
  ('Low', 72, 168);

INSERT INTO users (username, pw_hash)
VALUES
  ('admin', '$argon2id$v=19$m=65536,t=3,p=4$NTg5TGx4bkJKeFRsYXBCZQ$+LIBPJxZX3K2lUiNwbW9TRwYL4WLAYO0Wrk+9+k3fE8'),
  ('alice', '$argon2id$v=19$m=65536,t=3,p=4$NTg5TGx4bkJKeFRsYXBCZQ$qjQZ5m/06iE3K0vOPPKaXlXe7dI/Rr7N5mZxtHgycE8'),
  ('bob', '$argon2id$v=19$m=65536,t=3,p=4$NTg5TGx4bkJKeFRsYXBCZQ$dEgcly+x+doJN2XPesj/ZZGy1jGoQQkVNqgwPY8PrgY')