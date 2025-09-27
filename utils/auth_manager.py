import psycopg2
from psycopg2.extras import RealDictCursor
import hashlib
import re
from dotenv import load_dotenv
import os

load_dotenv()

class AuthManager:
    def __init__(self):
        # Configure your PostgreSQL connection
        self.conn = psycopg2.connect(
            host=os.getenv("DB_HOST"),
            database=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD")
        )
        self.cursor = self.conn.cursor(cursor_factory=RealDictCursor)

    # --- Helper: hash passwords ---
    def hash_password(self, password: str) -> str:
        return hashlib.sha256(password.encode()).hexdigest()

    # --- Validate password strength ---
    def validate_password_strength(self, password: str) -> tuple[bool, str]:
        if len(password) < 8:
            return False, "Password must be at least 8 characters"
        if not re.search(r"[A-Z]", password):
            return False, "Include at least 1 uppercase letter"
        if not re.search(r"[a-z]", password):
            return False, "Include at least 1 lowercase letter"
        if not re.search(r"\d", password):
            return False, "Include at least 1 number"
        return True, "Strong password"

    # --- Register user ---
    def register_user(self, username: str, email: str, password: str) -> tuple[bool, str]:
        try:
            hashed_pw = self.hash_password(password)
            self.cursor.execute(
                "INSERT INTO users (username,email,password) VALUES (%s,%s,%s)",
                (username, email, hashed_pw)
            )
            self.conn.commit()
            return True, "User registered successfully"
        except psycopg2.errors.UniqueViolation:
            self.conn.rollback()
            return False, "Username or email already exists"
        except Exception as e:
            print("DB Error:", e)
            self.conn.rollback()
            return False, "Registration failed"

    # --- Login user ---
    def login_user(self, username: str, password: str) -> tuple[bool, str]:
        hashed_pw = self.hash_password(password)
        self.cursor.execute(
            "SELECT * FROM users WHERE username=%s AND password=%s",
            (username, hashed_pw)
        )
        user = self.cursor.fetchone()
        if user:
            return True, "Login successful"
        return False, "Invalid credentials"
