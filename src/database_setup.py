# src/database_setup.py

import sqlite3
import os
from datetime import datetime

class DatabaseSetup:
    """
    Handles the initial setup of the application's database with an advanced schema.
    This class creates the database file and all necessary tables for a multi-user
    budgeting application if they don't already exist.
    """

    def __init__(self, db_name="my_budget.db"):
        """
        Initializes the DatabaseSetup object.

        Args:
            db_name (str): The name of the database file to be created.
        """
        project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.db_path = os.path.join(project_dir, db_name)
        self.conn = None
        self.cursor = None

    def connect(self):
        """Establishes a connection to the database and enables foreign key support."""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.execute("PRAGMA foreign_keys = ON;") # Enable foreign key constraints
            self.cursor = self.conn.cursor()
            print(f"Successfully connected to database at {self.db_path}")
        except sqlite3.Error as e:
            print(f"Error connecting to database: {e}")
            raise

    def create_tables(self):
        """Creates all the required tables based on the new, advanced schema."""
        if not self.cursor:
            print("Cannot create tables without a database connection.")
            return

        try:
            # 1. Users Table
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL UNIQUE,
                    password_hash TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
            ''')
            print("Table 'users' created or already exists.")

            # 2. Categories Table
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    type TEXT NOT NULL CHECK(type IN ('income', 'expense')),
                    icon TEXT,
                    user_id INTEGER,
                    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
                    UNIQUE(name, user_id)
                )
            ''')
            print("Table 'categories' created or already exists.")

            # 3. Subcategories Table
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS subcategories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    category_id INTEGER NOT NULL,
                    user_id INTEGER,
                    FOREIGN KEY (category_id) REFERENCES categories (id) ON DELETE CASCADE,
                    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
                    UNIQUE(name, category_id, user_id)
                )
            ''')
            print("Table 'subcategories' created or already exists.")
            
            # 4. Recurring Transactions Table
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS recurring_transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    amount REAL NOT NULL,
                    frequency TEXT NOT NULL CHECK(frequency IN ('daily', 'weekly', 'monthly', 'yearly')),
                    next_date TEXT NOT NULL,
                    category_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    FOREIGN KEY (category_id) REFERENCES categories (id),
                    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
                )
            ''')
            print("Table 'recurring_transactions' created or already exists.")

            # 5. Transactions Table
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    amount REAL NOT NULL,
                    date TEXT NOT NULL,
                    note TEXT,
                    payment_method TEXT,
                    user_id INTEGER NOT NULL,
                    category_id INTEGER NOT NULL,
                    subcategory_id INTEGER,
                    recurring_id INTEGER,
                    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
                    FOREIGN KEY (category_id) REFERENCES categories (id),
                    FOREIGN KEY (subcategory_id) REFERENCES subcategories (id),
                    FOREIGN KEY (recurring_id) REFERENCES recurring_transactions (id) ON DELETE SET NULL
                )
            ''')
            print("Table 'transactions' created or already exists.")

            self.conn.commit()
        except sqlite3.Error as e:
            print(f"Error creating tables: {e}")
            self.conn.rollback()
            raise

    def seed_default_data(self):
        """Inserts a set of default categories and subcategories."""
        if not self.cursor:
            print("Cannot seed data without a database connection.")
            return

        try:
            # Seed default categories (user_id is NULL for these)
            default_categories = [
                ('Salary', 'income', '💰'), ('Freelance', 'income', '💼'), ('Investment', 'income', '📈'),
                ('Gifts', 'income', '🎁'), ('Refunds', 'income', '🔙'),
                ('Rent/Mortgage', 'expense', '🏠'), ('Groceries', 'expense', '🛒'), ('Transport', 'expense', '🚗'),
                ('Utilities', 'expense', '💡'), ('Entertainment', 'expense', '🎬'), ('Dining Out', 'expense', '🍔'),
                ('Health', 'expense', '❤️'), ('Insurance', 'expense', '🛡️'), ('Shopping', 'expense', '🛍️'),
                ('Education', 'expense', '🎓'), ('Kids', 'expense', '👶'), ('Pets', 'expense', '🐾'),
                ('Travel', 'expense', '✈️'), ('Savings', 'expense', '🏦'), ('Donations', 'expense', '🤝'),
                ('Other', 'expense', '❓')
            ]
            self.cursor.executemany(
                "INSERT OR IGNORE INTO categories (name, type, icon) VALUES (?, ?, ?)",
                default_categories
            )
            print(f"Seeded {len(default_categories)} default categories.")

            # Seed example subcategories for 'Shopping'
            # First, get the category_id for 'Shopping'
            self.cursor.execute("SELECT id FROM categories WHERE name = 'Shopping' AND user_id IS NULL")
            shopping_cat_id_row = self.cursor.fetchone()
            if shopping_cat_id_row:
                shopping_cat_id = shopping_cat_id_row[0]
                default_subcategories = [
                    ('Electronics', shopping_cat_id), ('Clothing', shopping_cat_id),
                    ('Beauty & Self-care', shopping_cat_id), ('Home & Decor', shopping_cat_id),
                    ('Tools & DIY', shopping_cat_id), ('Gifts', shopping_cat_id)
                ]
                self.cursor.executemany(
                    "INSERT OR IGNORE INTO subcategories (name, category_id) VALUES (?, ?)",
                    default_subcategories
                )
                print(f"Seeded {len(default_subcategories)} default subcategories for 'Shopping'.")

            self.conn.commit()
        except sqlite3.Error as e:
            print(f"Error seeding data: {e}")
            self.conn.rollback()
            raise

    def close(self):
        """Closes the database connection."""
        if self.conn:
            self.conn.close()
            print("Database connection closed.")

    def run(self):
        """Executes the full database setup process."""
        try:
            self.connect()
            self.create_tables()
            self.seed_default_data()
        except sqlite3.Error as e:
            print(f"A database error occurred: {e}")
        finally:
            self.close()


if __name__ == '__main__':
    # This block runs only when the script is executed directly.
    print("Running database setup...")
    setup = DatabaseSetup()
    setup.run()
    print("Database setup complete.")
