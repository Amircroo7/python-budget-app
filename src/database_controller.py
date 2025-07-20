# src/database_controller.py

import sqlite3
import os
import sys # Import sys to check for bundled app
import hashlib 
from datetime import datetime
import pandas as pd # type: ignore

class DatabaseController:
    """
    Handles all database operations for the Budget App.
    This class acts as an interface between the application logic and the SQLite database,
    managing all CRUD (Create, Read, Update, Delete) operations.
    """

    def __init__(self, db_name="my_budget.db"):
        """
        Initializes the DatabaseController and sets the path to the database file.
        This now correctly handles paths for both normal execution and a bundled .exe.
        """
        # *** MODIFIED CODE BLOCK ***
        # This logic determines the correct base path whether running as a script
        # or as a frozen .exe file created by PyInstaller.
        if getattr(sys, 'frozen', False):
            # If the application is run as a bundle, the PyInstaller bootloader
            # extends the sys module by a flag frozen=True and sets the app 
            # path into variable _MEIPASS'.
            base_path = sys._MEIPASS
        else:
            # Running as a normal .py script. The path is relative to this file.
            # Go up two directories from src/ to the project root.
            base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # The database path is now correctly set in both scenarios.
        self.db_path = os.path.join(base_path, db_name)
        # --- END OF MODIFIED BLOCK ---

    def _get_connection(self):
        """
        Establishes and returns a database connection.
        Enables foreign key support for the connection.
        """
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.row_factory = sqlite3.Row 
        return conn

    # --- User Management Methods ---

    def _hash_password(self, password):
        """Hashes a password using SHA-256."""
        return hashlib.sha256(password.encode('utf-8')).hexdigest()

    def add_user(self, username, password):
        """
        Adds a new user to the database.
        Returns the ID of the new user, or None if the username already exists.
        """
        password_hash = self._hash_password(password)
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sql = "INSERT INTO users (username, password_hash, created_at) VALUES (?, ?, ?)"
        
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(sql, (username, password_hash, created_at))
                conn.commit()
                return cursor.lastrowid
        except sqlite3.IntegrityError:
            print(f"Error: Username '{username}' already exists.")
            return None
        except sqlite3.Error as e:
            print(f"Database error in add_user: {e}")
            return None

    def verify_user(self, username, password):
        """
        Verifies a user's login credentials.
        Returns a dictionary with user data if successful, otherwise None.
        """
        password_hash = self._hash_password(password)
        sql = "SELECT * FROM users WHERE username = ? AND password_hash = ?"
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, (username, password_hash))
            user_row = cursor.fetchone()
            
            if user_row:
                return dict(user_row)
            return None

    # --- Category Management Methods ---

    def get_categories(self, user_id, category_type='expense'):
        """
        Fetches all categories for a given type (default + user-specific).
        Returns a list of dictionaries, where each dictionary represents a category.
        """
        sql = """
            SELECT id, name, icon FROM categories 
            WHERE type = ? AND (user_id = ? OR user_id IS NULL)
            ORDER BY name
        """
        categories = []
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(sql, (category_type, user_id))
                rows = cursor.fetchall()
                for row in rows:
                    categories.append(dict(row))
            return categories
        except sqlite3.Error as e:
            print(f"Database error in get_categories: {e}")
            return []

    # --- Transaction Management Methods ---

    def add_transaction(self, user_id, category_id, amount, date, note=None, payment_method=None, subcategory_id=None):
        """Adds a new transaction to the database."""
        sql = """
            INSERT INTO transactions (user_id, category_id, subcategory_id, amount, date, note, payment_method)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(sql, (user_id, category_id, subcategory_id, amount, date, note, payment_method))
                conn.commit()
                return cursor.lastrowid
        except sqlite3.Error as e:
            print(f"Database error in add_transaction: {e}")
            return None

    def export_transactions_to_excel(self, user_id, file_path):
        """
        Fetches all transactions for a user and exports them to an Excel file.
        """
        sql = """
            SELECT 
                t.date,
                c.name AS category,
                sc.name AS subcategory,
                t.amount,
                t.payment_method,
                t.note,
                c.type
            FROM transactions t
            JOIN categories c ON t.category_id = c.id
            LEFT JOIN subcategories sc ON t.subcategory_id = sc.id
            WHERE t.user_id = ?
            ORDER BY t.date DESC
        """
        try:
            with self._get_connection() as conn:
                df = pd.read_sql_query(sql, conn, params=(user_id,))
            
            df.to_excel(file_path, index=False, engine='openpyxl')
            print(f"Successfully exported data to {file_path}")
            return True
        except Exception as e:
            print(f"An error occurred during Excel export: {e}")
            return False

# Example usage block is omitted for brevity but would be here for testing.
