-- Схема базы данных для 3D Printer AI Assistant

-- Users
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    telegram_id INTEGER UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    preferences JSONB DEFAULT '{}'
);

-- Sessions (диалоги)
CREATE TABLE IF NOT EXISTS sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP,
    printer_model VARCHAR(100),
    material VARCHAR(50)
);

-- Messages (история)
CREATE TABLE IF NOT EXISTS messages (
    id SERIAL PRIMARY KEY,
    session_id INTEGER REFERENCES sessions(id),
    role VARCHAR(20) NOT NULL,  -- "user", "assistant", "system"
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    tokens_used INTEGER
);

-- Prints (Записи о печатях)
CREATE TABLE IF NOT EXISTS prints (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    gcode_hash VARCHAR(64),  -- SHA256 файла
    material VARCHAR(50),
    estimated_time_hours FLOAT,
    estimated_weight_g FLOAT,
    success BOOLEAN,
    notes TEXT,
    images_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Print Images
CREATE TABLE IF NOT EXISTS print_images (
    id SERIAL PRIMARY KEY,
    print_id INTEGER REFERENCES prints(id),
    image_path VARCHAR(500) NOT NULL,
    analysis_result JSONB,
    defect_detected BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tool invocations (Логирование инструментов)
CREATE TABLE IF NOT EXISTS tool_invocations (
    id SERIAL PRIMARY KEY,
    session_id INTEGER REFERENCES sessions(id),
    tool_name VARCHAR(100) NOT NULL,
    input_data JSONB,
    output_data JSONB,
    execution_time_ms INTEGER,
    success BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Индексы для производительности
CREATE INDEX IF NOT EXISTS idx_users_telegram_id ON users(telegram_id);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_messages_session_id ON messages(session_id);
CREATE INDEX IF NOT EXISTS idx_prints_user_id ON prints(user_id);
CREATE INDEX IF NOT EXISTS idx_prints_gcode_hash ON prints(gcode_hash);
CREATE INDEX IF NOT EXISTS idx_tool_invocations_session_id ON tool_invocations(session_id);
CREATE INDEX IF NOT EXISTS idx_tool_invocations_tool_name ON tool_invocations(tool_name);

