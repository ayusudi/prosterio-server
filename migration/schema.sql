-- Migration for Talent Recomendation System
CREATE TABLE Users (
    id INT PRIMARY KEY AUTOINCREMENT,
	name VARCHAR NOT NULL,
	email VARCHAR UNIQUE NOT NULL,
    created_at TIMESTAMP_TZ DEFAULT CURRENT_TIMESTAMP(),
    updated_at TIMESTAMP_TZ DEFAULT CURRENT_TIMESTAMP(),
	role VARCHAR NOT NULL,
    is_deleted BOOLEAN DEFAULT FALSE,
    deleted_at TIMESTAMP_TZ DEFAULT NULL,
	password BINARY,
	otp_code VARCHAR(6),
	expired_otp TIMESTAMP_NTZ
)

CREATE TABLE Employees (
    id INT PRIMARY KEY AUTOINCREMENT,
    full_name VARCHAR NOT NULL,
    email VARCHAR UNIQUE NOT NULL,
    job_title VARCHAR NOT NULL,
    promotion_years INT,
    profile TEXT,
    skills VARIANT,
    professional_experiences VARIANT,
    educations VARIANT,
    publications VARIANT,
    distinctions VARIANT,
    certifications VARIANT,
    file_data BINARY,
    file_url TEXT,
    created_at TIMESTAMP_TZ DEFAULT CURRENT_TIMESTAMP(),
    updated_at TIMESTAMP_TZ DEFAULT CURRENT_TIMESTAMP(),
    user_id INT REFERENCES Users(id) ON DELETE CASCADE
);

CREATE TABLE Content_Chunks (
    id INT PRIMARY KEY AUTOINCREMENT,
    chunk_text TEXT NOT NULL,
    type VARCHAR NOT NULL,
    user_id INT REFERENCES Users(id) ON DELETE CASCADE,
    employee_id INT REFERENCES Employees(id) ON DELETE SET NULL
);






CREATE TABLE Chats (
    id INT PRIMARY KEY AUTOINCREMENT,
    title VARCHAR NOT NULL,
    chats VARIANT,
    user_id INT REFERENCES Users(id) ON DELETE CASCADE,
    created_at TIMESTAMP_TZ DEFAULT CURRENT_TIMESTAMP(),
    updated_at TIMESTAMP_TZ DEFAULT CURRENT_TIMESTAMP(),
    is_deleted BOOLEAN DEFAULT FALSE,
    deleted_at TIMESTAMP_TZ DEFAULT NULL
);

-- Migration for LLM Evaluations
CREATE TABLE EVALUATIONS (
    id INTEGER AUTOINCREMENT PRIMARY KEY,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    cortex_coherence FLOAT,
    groundedness FLOAT,
    relevance FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
);

CREATE TABLE LLM_EVALUATIONS (
    RUN_ID VARCHAR(36) PRIMARY KEY,
    TIMESTAMP TIMESTAMP_NTZ,
    USER_INPUT TEXT,
    MODEL_RESPONSE TEXT,
    LATENCY_SECONDS FLOAT,
    TOKEN_COUNT INTEGER,
    MODEL_NAME VARCHAR(100),
    STATUS VARCHAR(20),
    ERROR_MESSAGE TEXT
);
