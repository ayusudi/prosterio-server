CREATE TABLE Users (
    id INT PRIMARY KEY AUTOINCREMENT,
	name VARCHAR NOT NULL,
	email VARCHAR UNIQUE NOT NULL,
    created_at TIMESTAMP_TZ DEFAULT CURRENT_TIMESTAMP(),
    updated_at TIMESTAMP_TZ DEFAULT CURRENT_TIMESTAMP(),
	role VARCHAR NOT NULL,
    is_deleted BOOLEAN DEFAULT FALSE,
    deleted_at TIMESTAMP_TZ DEFAULT NULL
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
    resign_status BOOLEAN DEFAULT FALSE,
    resign_date TIMESTAMP_TZ DEFAULT NULL,
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