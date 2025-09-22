#!/usr/bin/env python3
"""
Simple database setup script for OceanScope.
This script creates the PostgreSQL database tables using psql directly.
"""

import subprocess
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env if present
load_dotenv()


def run_psql_command(sql_command, *, host: str, port: str, database: str, user: str, password: str):
    """Run a SQL command using psql."""
    try:
        # Set PGPASSWORD environment variable
        env = os.environ.copy()
        env['PGPASSWORD'] = password or ''
        
        # Run psql command
        result = subprocess.run(
            ['psql', '-h', host, '-p', str(port), '-U', user, '-d', database, '-c', sql_command],
            env=env,
            capture_output=True,
            text=True,
            check=True
        )
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        return False, e.stderr
    except FileNotFoundError:
        return False, "psql command not found. Please install PostgreSQL client tools."


def setup_database():
    """Set up the PostgreSQL database with schema."""
    print("🌊 OceanScope Database Setup (Simple)")
    print("=" * 50)
    
    # Database connection parameters from environment
    host = os.getenv('DB_HOST', 'localhost')
    port = os.getenv('DB_PORT', '5432')
    database = os.getenv('DB_NAME', 'oceanscope')
    user = os.getenv('DB_USER', 'postgres')
    password = os.getenv('DB_PASSWORD', '')
    
    print(f"📊 Connecting to database: {database}")
    print(f"🏠 Host: {host}:{port}")
    print(f"👤 User: {user}")
    
    # Test connection
    print("\n🔌 Testing database connection...")
    success, output = run_psql_command(
        "SELECT 1;",
        host=host, port=port, database=database, user=user, password=password
    )
    if not success:
        print(f"❌ Database connection failed: {output}")
        return False
    print("✅ Database connection established!")
    
    # Create tables one by one
    print("\n📋 Creating database tables...")
    
    # 1. Create message_type_enum
    print("   Creating message_type_enum...")
    success, output = run_psql_command(
        """DO $$ BEGIN
            CREATE TYPE message_type_enum AS ENUM ('user', 'assistant');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;""",
        host=host, port=port, database=database, user=user, password=password
    )
    if not success and "duplicate_object" not in output:
        print(f"   ⚠️  Warning: {output}")
    else:
        print("   ✅ message_type_enum created")
    
    # 2. Create user_role_enum
    print("   Creating user_role_enum...")
    success, output = run_psql_command(
        """DO $$ BEGIN
            CREATE TYPE user_role_enum AS ENUM ('user', 'admin', 'moderator');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;""",
        host=host, port=port, database=database, user=user, password=password
    )
    if not success and "duplicate_object" not in output:
        print(f"   ⚠️  Warning: {output}")
    else:
        print("   ✅ user_role_enum created")
    
    # 3. Create users table
    print("   Creating users table...")
    success, output = run_psql_command(
        """CREATE TABLE IF NOT EXISTS users (
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
        );""",
        host=host, port=port, database=database, user=user, password=password
    )
    if not success and "already exists" not in output:
        print(f"   ⚠️  Warning: {output}")
    else:
        print("   ✅ users table created")
    
    # 4. Create user_profiles table
    print("   Creating user_profiles table...")
    success, output = run_psql_command(
        """CREATE TABLE IF NOT EXISTS user_profiles (
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
        );""",
        host=host, port=port, database=database, user=user, password=password
    )
    if not success and "already exists" not in output:
        print(f"   ⚠️  Warning: {output}")
    else:
        print("   ✅ user_profiles table created")
    
    # 5. Create chat_sessions table
    print("   Creating chat_sessions table...")
    success, output = run_psql_command(
        """CREATE TABLE IF NOT EXISTS chat_sessions (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            session_name VARCHAR(100) NOT NULL,
            description TEXT,
            is_active BOOLEAN DEFAULT true,
            message_count INTEGER DEFAULT 0,
            last_message_at TIMESTAMP WITH TIME ZONE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );""",
        host=host, port=port, database=database, user=user, password=password
    )
    if not success and "already exists" not in output:
        print(f"   ⚠️  Warning: {output}")
    else:
        print("   ✅ chat_sessions table created")
    
    # 6. Create chat_messages table
    print("   Creating chat_messages table...")
    success, output = run_psql_command(
        """CREATE TABLE IF NOT EXISTS chat_messages (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            session_id UUID NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
            message_type message_type_enum NOT NULL,
            content TEXT NOT NULL,
            metadata JSONB,
            is_edited BOOLEAN DEFAULT false,
            edited_at TIMESTAMP WITH TIME ZONE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );""",
        host=host, port=port, database=database, user=user, password=password
    )
    if not success and "already exists" not in output:
        print(f"   ⚠️  Warning: {output}")
    else:
        print("   ✅ chat_messages table created")
    
    # 7. Create analysis_sessions table
    print("   Creating analysis_sessions table...")
    success, output = run_psql_command(
        """CREATE TABLE IF NOT EXISTS analysis_sessions (
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
        );""",
        host=host, port=port, database=database, user=user, password=password
    )
    if not success and "already exists" not in output:
        print(f"   ⚠️  Warning: {output}")
    else:
        print("   ✅ analysis_sessions table created")
    
    # 8. Create user_preferences table
    print("   Creating user_preferences table...")
    success, output = run_psql_command(
        """CREATE TABLE IF NOT EXISTS user_preferences (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            theme VARCHAR(20) DEFAULT 'dark',
            language VARCHAR(10) DEFAULT 'en',
            timezone VARCHAR(50) DEFAULT 'UTC',
            notification_settings JSONB DEFAULT '{}',
            analysis_settings JSONB DEFAULT '{}',
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );""",
        host=host, port=port, database=database, user=user, password=password
    )
    if not success and "already exists" not in output:
        print(f"   ⚠️  Warning: {output}")
    else:
        print("   ✅ user_preferences table created")
    
    # 9. Create indexes
    print("   Creating indexes...")
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);",
        "CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);",
        "CREATE INDEX IF NOT EXISTS idx_chat_sessions_user_id ON chat_sessions(user_id);",
        "CREATE INDEX IF NOT EXISTS idx_chat_messages_session_id ON chat_messages(session_id);",
        "CREATE INDEX IF NOT EXISTS idx_analysis_sessions_user_id ON analysis_sessions(user_id);"
    ]
    
    for index_sql in indexes:
        success, output = run_psql_command(index_sql, host=host, port=port, database=database, user=user, password=password)
        if not success and "already exists" not in output:
            print(f"   ⚠️  Warning: {output}")
    
    print("   ✅ Indexes created")
    
    # 10. Insert default admin user
    print("   Creating default admin user...")
    success, output = run_psql_command(
        """INSERT INTO users (username, email, password_hash, role, is_active, email_verified) 
        VALUES ('admin', 'admin@oceanscope.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/8KzKz2K', 'admin', true, true)
        ON CONFLICT (username) DO NOTHING;""",
        host=host, port=port, database=database, user=user, password=password
    )
    if not success and "duplicate key" not in output:
        print(f"   ⚠️  Warning: {output}")
    else:
        print("   ✅ Default admin user created")
    
    # Verify tables were created
    print("\n🔍 Verifying table creation...")
    success, output = run_psql_command(
        "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' AND table_name IN ('users', 'user_profiles', 'chat_sessions', 'chat_messages', 'analysis_sessions', 'user_preferences') ORDER BY table_name;",
        host=host, port=port, database=database, user=user, password=password
    )
    
    if success:
        print("✅ OceanScope tables created successfully!")
        print("📋 Created tables:")
        for line in output.split('\n'):
            if line.strip() and not line.startswith('table_name') and not line.startswith('(') and not line.startswith('-'):
                print(f"   - {line.strip()}")
    else:
        print(f"❌ Error verifying tables: {output}")
        return False
    
    print("\n🎉 Database setup completed successfully!")
    print("\n📝 Next steps:")
    print("   1. Run the application: streamlit run app.py")
    print("   2. Create your first user account through the web interface")
    print("   3. Start using OceanScope with PostgreSQL!")
    
    return True


def main():
    """Main function."""
    try:
        success = setup_database()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n❌ Setup cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
