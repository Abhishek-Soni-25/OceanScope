-- OceanScope PostgreSQL Database Schema (Simplified)
-- This file contains the essential database schema for the OceanScope application

-- Enable UUID extension for better primary keys
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create custom types
DO $$ BEGIN
    CREATE TYPE message_type_enum AS ENUM ('user', 'assistant');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE user_role_enum AS ENUM ('user', 'admin', 'moderator');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Users table - stores user account information
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(50),
    last_name VARCHAR(50),
    role user_role_enum DEFAULT 'user',
    is_active BOOLEAN DEFAULT true,
    email_verified BOOLEAN DEFAULT false,
    last_login TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- User profiles table - extended user information
CREATE TABLE IF NOT EXISTS user_profiles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    bio TEXT,
    organization VARCHAR(100),
    research_interests TEXT[],
    location VARCHAR(100),
    website VARCHAR(255),
    avatar_url VARCHAR(500),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Chat sessions table - stores chat conversation sessions
CREATE TABLE IF NOT EXISTS chat_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_name VARCHAR(100) NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT true,
    message_count INTEGER DEFAULT 0,
    last_message_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Chat messages table - stores individual messages in chat sessions
CREATE TABLE IF NOT EXISTS chat_messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
    message_type message_type_enum NOT NULL,
    content TEXT NOT NULL,
    metadata JSONB,
    is_edited BOOLEAN DEFAULT false,
    edited_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Data analysis sessions table - tracks data analysis activities
CREATE TABLE IF NOT EXISTS analysis_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_name VARCHAR(100) NOT NULL,
    data_source VARCHAR(100),
    profile_id VARCHAR(50),
    analysis_type VARCHAR(50),
    parameters JSONB,
    results JSONB,
    is_public BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- User preferences table - stores user application preferences
CREATE TABLE IF NOT EXISTS user_preferences (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    theme VARCHAR(20) DEFAULT 'dark',
    language VARCHAR(10) DEFAULT 'en',
    timezone VARCHAR(50) DEFAULT 'UTC',
    notification_settings JSONB DEFAULT '{}',
    analysis_settings JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at);

CREATE INDEX IF NOT EXISTS idx_user_profiles_user_id ON user_profiles(user_id);

CREATE INDEX IF NOT EXISTS idx_chat_sessions_user_id ON chat_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_chat_sessions_created_at ON chat_sessions(created_at);
CREATE INDEX IF NOT EXISTS idx_chat_sessions_updated_at ON chat_sessions(updated_at);

CREATE INDEX IF NOT EXISTS idx_chat_messages_session_id ON chat_messages(session_id);
CREATE INDEX IF NOT EXISTS idx_chat_messages_created_at ON chat_messages(created_at);
CREATE INDEX IF NOT EXISTS idx_chat_messages_type ON chat_messages(message_type);

CREATE INDEX IF NOT EXISTS idx_analysis_sessions_user_id ON analysis_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_analysis_sessions_created_at ON analysis_sessions(created_at);

CREATE INDEX IF NOT EXISTS idx_user_preferences_user_id ON user_preferences(user_id);

-- Insert default admin user (password: admin123 - change this in production!)
INSERT INTO users (username, email, password_hash, role, is_active, email_verified) 
VALUES ('admin', 'admin@oceanscope.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/8KzKz2K', 'admin', true, true)
ON CONFLICT (username) DO NOTHING;
