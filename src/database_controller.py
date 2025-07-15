# src/database_controller.py

import sqlite3
import os
import hashlib # For password hashing
from datetime import datetime

class DatabaseController:
    """
    Handles all database operations for the Budget App.
    This class acts as an interface between the application logic and the SQLite database,
    managing all CRUD (Create, Read, Update, Delete) operations.
    """

    def __init__(self, db_name="my_budget.db"):
        """
        Initializes the DatabaseController and sets the path to the database file.

        Args:
            db_name (str): The name of the database file.
        """
        project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.db_path = os.path.join(project_dir, db_name)

    def _get_connection(self):
        """
        Establishes and returns a database connection.
        Enables foreign key support for the connection.
        """
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON;")
        # Return rows as dictionaries or Row objects for easier access by column name
        conn.row_factory = sqlite3.Row 
        return conn

    # --- User Management Methods ---

    def _hash_password(self, password):
        """Hashes a password using SHA-256."""
        return hashlib.sha256(password.encode('utf-8')).hexdigest()

    def add_user(self, username, password):
        """
        Adds a new user to the database.

        Args:
            username (str): The desired username.
            password (str): The user's plain-text password.

        Returns:
            int or None: The ID of the new user, or None if the username already exists.
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
            # This error occurs if the username is not unique.
            print(f"Error: Username '{username}' already exists.")
            return None
        except sqlite3.Error as e:
            print(f"Database error in add_user: {e}")
            return None

    def verify_user(self, username, password):
        """
        Verifies a user's login credentials.

        Args:
            username (str): The username to verify.
            password (str): The password to check.

        Returns:
            dict or None: A dictionary with user data if successful, otherwise None.
        """
        password_hash = self._hash_password(password)
        sql = "SELECT * FROM users WHERE username = ? AND password_hash = ?"
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, (username, password_hash))
            user_row = cursor.fetchone()
            
            if user_row:
                # Convert the sqlite3.Row object to a standard dictionary
                return dict(user_row)
            return None

    # --- Category Management Methods ---

    def get_categories(self, user_id, category_type='expense'):
        """
        Fetches all categories for a given type (default + user-specific).

        Args:
            user_id (int): The ID of the current user.
            category_type (str): 'income' or 'expense'.

        Returns:
            list: A list of dictionaries, where each dictionary represents a category.
        """
        # SQL to get default categories (user_id IS NULL) AND user's custom categories
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

# --- Example Usage ---
if __name__ == '__main__':
    # This block demonstrates how to use the controller.
    # It will only run when you execute this file directly.
    
    controller = DatabaseController()

    print("\n--- Testing User Management ---")
    # Try adding a new user
    new_user_id = controller.add_user("testuser", "password123")
    if new_user_id:
        print(f"Successfully added new user with ID: {new_user_id}")
    
    # Try adding the same user again (should fail)
    controller.add_user("testuser", "password123")

    # Verify the user
    verified_user = controller.verify_user("testuser", "password123")
    if verified_user:
        print(f"User 'testuser' verified successfully. User data: {verified_user}")
        current_user_id = verified_user['id']

        print("\n--- Testing Category Management ---")
        # Get expense categories for the verified user
        expense_cats = controller.get_categories(current_user_id, 'expense')
        print(f"Found {len(expense_cats)} expense categories:")
        for cat in expense_cats:
            print(f"  - {cat['icon']} {cat['name']} (ID: {cat['id']})")

        # Get income categories for the verified user
        income_cats = controller.get_categories(current_user_id, 'income')
        print(f"\nFound {len(income_cats)} income categories:")
        for cat in income_cats:
            print(f"  - {cat['icon']} {cat['name']} (ID: {cat['id']})")
    else:
        print("User verification failed.")

