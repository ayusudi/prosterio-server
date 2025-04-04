CREATE TABLE Users (
    id INT PRIMARY KEY AUTOINCREMENT,
    name VARCHAR NOT NULL,
    email VARCHAR UNIQUE NOT NULL,
    password BINARY(60); NOT NULL,
    auth_firebase BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP_TZ DEFAULT CURRENT_TIMESTAMP(),
    updated_at TIMESTAMP_TZ DEFAULT CURRENT_TIMESTAMP(),
    role VARCHAR NOT NULL,
    is_deleted BOOLEAN DEFAULT FALSE,
    date_deleted TIMESTAMP_TZ DEFAULT NULL
);

CREATE TABLE Employees (
    id INT PRIMARY KEY AUTOINCREMENT,
    full_name VARCHAR NOT NULL,
    job_title VARCHAR NOT NULL,
    email VARCHAR UNIQUE NOT NULL,
    skills VARIANT,
    file_data BINARY,
    file_url TEXT,
    created_at TIMESTAMP_TZ DEFAULT CURRENT_TIMESTAMP(),
    updated_at TIMESTAMP_TZ DEFAULT CURRENT_TIMESTAMP(),
    resign_status BOOLEAN DEFAULT FALSE,
    resign_date TIMESTAMP_TZ DEFAULT NULL,
    user_id INT REFERENCES Users(id) ON DELETE CASCADE
);

CREATE TABLE Clients (
    id INT PRIMARY KEY AUTOINCREMENT,
    company_name VARCHAR NOT NULL,
    created_at TIMESTAMP_TZ DEFAULT CURRENT_TIMESTAMP(),
    updated_at TIMESTAMP_TZ DEFAULT CURRENT_TIMESTAMP(),
    user_id INT REFERENCES Users(id) ON DELETE CASCADE
);

CREATE TABLE Projects (
    id INT PRIMARY KEY AUTOINCREMENT,
    project_name VARCHAR NOT NULL,
    detail_project TEXT,
    requirements TEXT,
    location VARCHAR,
    hired_count INT DEFAULT 1,
    max_stage INT DEFAULT 1,
    stages VARIANT DEFAULT ['screening_cv'],
    onsite_status BOOLEAN DEFAULT TRUE, 
    project_month VARCHAR,
    project_year INT DEFAULT 2025,
    start_date DATE,
    end_date DATE,
    created_at TIMESTAMP_TZ DEFAULT CURRENT_TIMESTAMP(),
    updated_at TIMESTAMP_TZ DEFAULT CURRENT_TIMESTAMP(),
    client_id INT REFERENCES Clients(id) ON DELETE CASCADE,
    archived BOOLEAN DEFAULT FALSE
);

CREATE TABLE Interview_Stages (
    id INT PRIMARY KEY AUTOINCREMENT,
    stage VARCHAR NOT NULL,
    status VARCHAR NOT NULL,
    notes TEXT,
    historical_notes VARIANT,
    created_at TIMESTAMP_TZ DEFAULT CURRENT_TIMESTAMP(),
    updated_at TIMESTAMP_TZ DEFAULT CURRENT_TIMESTAMP(),
    project_id INT REFERENCES Projects(id) ON DELETE CASCADE,
    employee_id INT REFERENCES Employees(id) ON DELETE SET NULL,
    user_id INT REFERENCES Users(id) ON DELETE CASCADE
);

CREATE TABLE Content_Chunks (
    id INT PRIMARY KEY AUTOINCREMENT,
    chunk_text TEXT NOT NULL,
    type VARCHAR NOT NULL,
    user_id INT REFERENCES Users(id) ON DELETE CASCADE,
    employee_id INT REFERENCES Employees(id) ON DELETE SET NULL
);

