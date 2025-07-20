# src/database_controller.py

import sqlite3
import os
import hashlib # For password hashing
from datetime import datetime
import pandas as pd # Import pandas

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

        Args:
            user_id (int): The ID of the user whose data to export.
            file_path (str): The full path for the output Excel file.

        Returns:
            bool: True if export was successful, False otherwise.
        """
        # This SQL query joins the transactions table with categories and subcategories
        # to get human-readable names instead of just IDs.
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
                # Use pandas to read the SQL query results directly into a DataFrame
                df = pd.read_sql_query(sql, conn, params=(user_id,))
            
            # Use pandas to write the DataFrame to an Excel file
            df.to_excel(file_path, index=False, engine='openpyxl')
            print(f"Successfully exported data to {file_path}")
            return True
        except Exception as e:
            print(f"An error occurred during Excel export: {e}")
            return False


# --- Example Usage ---
if __name__ == '__main__':
    controller = DatabaseController()
    
    print("\n--- Setting up test user ---")
    # Ensure our test user exists
    controller.add_user("testuser", "password123") 
    verified_user = controller.verify_user("testuser", "password123")
    
    if verified_user:
        current_user_id = verified_user['id']
        print(f"Verified user 'testuser' with ID: {current_user_id}")

        print("\n--- Adding sample transactions ---")
        # Get some category IDs to use for our sample data
        groceries_cat = next((c for c in controller.get_categories(current_user_id, 'expense') if c['name'] == 'Groceries'), None)
        salary_cat = next((c for c in controller.get_categories(current_user_id, 'income') if c['name'] == 'Salary'), None)
        
        if groceries_cat and salary_cat:
            # Add an income transaction
            controller.add_transaction(current_user_id, salary_cat['id'], 5000, '2025-07-01', 'Monthly Paycheck', 'Direct Deposit')
            # Add some expense transactions
            controller.add_transaction(current_user_id, groceries_cat['id'], 75.50, '2025-07-05', 'Weekly groceries', 'Credit Card')
            controller.add_transaction(current_user_id, groceries_cat['id'], 120.00, '2025-07-12', 'Groceries for party', 'Debit Card')
            print("Sample transactions added.")
        else:
            print("Could not find 'Groceries' or 'Salary' category to add sample data.")

        print("\n--- Testing Export Functionality ---")
        # Define the output file path (it will be in the main BudgetApp folder)
        export_path = os.path.join(os.path.dirname(controller.db_path), 'budget_export.xlsx')
        controller.export_transactions_to_excel(current_user_id, export_path)
    else:
        print("Could not verify test user.")

