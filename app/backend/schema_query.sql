DROP DATABASE IF EXISTS it_db;
CREATE DATABASE it_db;

USE it_db;

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
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
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