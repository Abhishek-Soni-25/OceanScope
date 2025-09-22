#!/usr/bin/env python3
"""
Database setup script for OceanScope.
This script initializes the PostgreSQL database with the required schema.
It safely creates tables without affecting existing data.
"""

import asyncio
import sys
import os
import logging
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from database.postgresql_manager import PostgreSQLManager
from config.database_config import get_database_config


async def setup_database():
    """Set up the PostgreSQL database with schema."""
    print("🌊 OceanScope Database Setup")
    print("=" * 50)
    
    # Get database configuration
    config = get_database_config()
    print(f"📊 Connecting to database: {config.database}")
    print(f"🏠 Host: {config.host}:{config.port}")
    print(f"👤 User: {config.username}")
    
    # Initialize database manager
    db_manager = PostgreSQLManager(config)
    
    try:
        # Initialize connection pool
        print("\n🔌 Initializing database connection...")
        await db_manager.initialize()
        print("✅ Database connection established!")
        
        # Check if tables already exist
        print("\n🔍 Checking existing tables...")
        existing_tables = await db_manager.execute_query(
            "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'",
            fetch=True
        )
        
        if existing_tables:
            print(f"ℹ️  Found {len(existing_tables)} existing tables:")
            for table in existing_tables:
                print(f"   - {table['table_name']}")
            
            # Check if OceanScope tables already exist
            oceanscope_tables = ['users', 'user_profiles', 'chat_sessions', 'chat_messages', 'analysis_sessions', 'user_preferences']
            existing_oceanscope_tables = [table['table_name'] for table in existing_tables if table['table_name'] in oceanscope_tables]
            
            if existing_oceanscope_tables:
                print(f"\n⚠️  OceanScope tables already exist: {', '.join(existing_oceanscope_tables)}")
                print("ℹ️  Skipping table creation to preserve existing data.")
                print("✅ Database setup completed (using existing tables)!")
                return True
            else:
                print("\nℹ️  No OceanScope tables found. Creating new tables...")
        else:
            print("ℹ️  No existing tables found. Creating new tables...")
        
        # Use the simple setup approach
        print("\n📋 Creating database schema...")
        print("ℹ️  Using simple setup approach...")
        
        # Import and run the simple setup
        import subprocess
        import os
        
        # Set up environment
        env = os.environ.copy()
        env['PGPASSWORD'] = self.config.password
        
        # Run the simple setup script
        result = subprocess.run(
            [sys.executable, str(project_root / "scripts" / "setup_database_simple.py")],
            capture_output=True,
            text=True,
            env=env
        )
        
        if result.returncode == 0:
            print("✅ Database schema setup completed!")
        else:
            print(f"❌ Database schema setup failed: {result.stderr}")
            return False
        
        # Verify tables were created
        print("\n🔍 Verifying table creation...")
        tables = await db_manager.execute_query(
            "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'",
            fetch=True
        )
        
        print(f"✅ Created {len(tables)} tables:")
        for table in tables:
            print(f"   - {table['table_name']}")
        
        # Test basic functionality
        print("\n🧪 Testing basic functionality...")
        
        # Test user creation
        test_user_id = await db_manager.create_user(
            username="test_user",
            email="test@example.com",
            password_hash="$2b$12$test_hash_here"
        )
        print(f"   ✅ User creation test passed (ID: {test_user_id})")
        
        # Test chat session creation
        session_id = await db_manager.create_chat_session(
            user_id=test_user_id,
            session_name="Test Session"
        )
        print(f"   ✅ Chat session creation test passed (ID: {session_id})")
        
        # Test message creation
        message_id = await db_manager.add_chat_message(
            session_id=session_id,
            message_type="user",
            content="Test message"
        )
        print(f"   ✅ Message creation test passed (ID: {message_id})")
        
        # Clean up test data
        await db_manager.execute_query("DELETE FROM users WHERE username = 'test_user'")
        print("   🧹 Test data cleaned up")
        
        print("\n🎉 Database setup completed successfully!")
        print("\n📝 Next steps:")
        print("   1. Run the application: streamlit run app.py")
        print("   2. Create your first user account through the web interface")
        print("   3. Start using OceanScope with PostgreSQL!")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Database setup failed: {e}")
        logging.error(f"Database setup error: {e}")
        return False
    
    finally:
        # Close database connection
        await db_manager.close()
        print("\n🔌 Database connection closed.")


async def main():
    """Main function."""
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    success = await setup_database()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
