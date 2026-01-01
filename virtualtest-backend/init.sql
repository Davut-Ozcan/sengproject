-- Users tablosu
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    role VARCHAR(50) DEFAULT 'Student',
    account_status VARCHAR(50) DEFAULT 'Active',
    verification_token VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Test Sessions tablosu
CREATE TABLE test_sessions (
    id SERIAL PRIMARY KEY,
    student_id INTEGER REFERENCES users(id),
    start_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completion_date TIMESTAMP,
    overall_cefr_level VARCHAR(10),
    is_completed BOOLEAN DEFAULT FALSE,
    overall_score FLOAT
);

-- Module Scores tablosu
CREATE TABLE module_scores (
    id SERIAL PRIMARY KEY,
    session_id INTEGER REFERENCES test_sessions(id),
    student_id INTEGER REFERENCES users(id),
    module_name VARCHAR(50) NOT NULL,
    score FLOAT,
    cefr_level VARCHAR(10),
    completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);