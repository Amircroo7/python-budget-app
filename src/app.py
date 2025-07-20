# src/app.py

# --- Kivy Imports ---
# App: The base class for any Kivy application.
# Layouts: BoxLayout, GridLayout are used to arrange widgets.
# Widgets: Label, TextInput, Spinner, Button, Popup are the UI elements we see.
# Window: Used to configure the application window, like setting its size.
from kivy.app import App # type: ignore
from kivy.uix.boxlayout import BoxLayout # type: ignore
from kivy.uix.gridlayout import GridLayout # type: ignore
from kivy.uix.label import Label # type: ignore
from kivy.uix.textinput import TextInput # type: ignore
from kivy.uix.spinner import Spinner # type: ignore
from kivy.uix.button import Button # type: ignore
from kivy.uix.popup import Popup # type: ignore
from kivy.core.window import Window # type: ignore

# --- Standard Library Imports ---
from datetime import datetime
import os

# --- Local Imports ---
# Import our custom class that handles all database interactions.
from database_controller import DatabaseController

# --- Window Configuration ---
# Set a default window size for a more mobile-like aspect ratio.
# This makes development on a desktop easier to visualize.
Window.size = (400, 600)

class BudgetApp(App):
    """
    This is the main application class. It inherits from Kivy's App class
    and is responsible for building and managing the entire user interface.
    """

    def build(self):
        """
        This is the core method of a Kivy App, called automatically on startup.
        It must return the single "root" widget for the entire application window.
        """
        self.title = "My Budget App"
        
        # --- Initialize Backend Controller ---
        self.db_controller = DatabaseController()
        # In a real app, this would be set after a login screen. For now, we hardcode it.
        self.user_id = 1 
        # This dictionary will map human-readable category names (e.g., "Groceries")
        # to their unique IDs in the database (e.g., 6). This is essential for saving transactions.
        self.categories_map = {} 

        # --- UI Layout Construction ---
        # The main layout is a vertical BoxLayout. Widgets are stacked from top to bottom.
        main_layout = BoxLayout(orientation='vertical', padding=15, spacing=10)
        
        # A GridLayout is perfect for forms, arranging widgets in a neat grid.
        # We define 2 columns. Widgets will be added left-to-right, top-to-bottom.
        form_layout = GridLayout(cols=2, spacing=10, size_hint_y=None, height=220)
        
        # --- Form Widgets ---
        form_layout.add_widget(Label(text="Type:", font_size='16sp'))
        self.type_spinner = Spinner(text='Expense', values=('Expense', 'Income'), font_size='16sp')
        self.type_spinner.bind(text=self.update_categories)
        form_layout.add_widget(self.type_spinner)

        form_layout.add_widget(Label(text="Category:", font_size='16sp'))
        self.category_spinner = Spinner(text='Select Category', values=(), font_size='16sp')
        form_layout.add_widget(self.category_spinner)

        form_layout.add_widget(Label(text="Amount:", font_size='16sp'))
        self.amount_input = TextInput(multiline=False, input_filter='float', hint_text='0.00', font_size='16sp')
        form_layout.add_widget(self.amount_input)

        form_layout.add_widget(Label(text="Date:", font_size='16sp'))
        self.date_input = TextInput(text=datetime.now().strftime("%Y-%m-%d %I:%M %p"), multiline=False, font_size='16sp')
        form_layout.add_widget(self.date_input)

        form_layout.add_widget(Label(text="Note:", font_size='16sp'))
        self.note_input = TextInput(multiline=False, hint_text='Optional description', font_size='16sp')
        form_layout.add_widget(self.note_input)

        main_layout.add_widget(form_layout)
        
        # --- Action Buttons ---
        button_layout = BoxLayout(size_hint_y=None, height=50, spacing=10)
        add_button = Button(text="Add Transaction", font_size='18sp')
        add_button.bind(on_press=self.add_transaction_callback)
        export_button = Button(text="Export Data", font_size='18sp')
        export_button.bind(on_press=self.export_data_callback)
        button_layout.add_widget(add_button)
        button_layout.add_widget(export_button)
        main_layout.add_widget(button_layout)

        # --- Transaction List (Placeholder) ---
        # This label fills the remaining vertical space.
        # size_hint_y=1.0 tells it to take up all available vertical space.
        main_layout.add_widget(Label(text="Recent transactions will appear here...", size_hint_y=1.0))
        
        # --- Status Bar ---
        self.status_bar = Label(text="Ready", size_hint_y=None, height=30, halign='left', valign='middle', padding_x=10)
        self.status_bar.bind(texture_size=self.status_bar.setter('size'))
        main_layout.add_widget(self.status_bar)

        # --- Initial Data Load ---
        # We must call this once at the start to populate the category spinner.
        self.update_categories(self.type_spinner, self.type_spinner.text)
        
        return main_layout

    def update_categories(self, spinner, text):
        """
        Called when the 'Type' spinner changes. Fetches categories from the DB
        and updates the 'Category' spinner's choices.
        """
        category_type = text.lower()
        categories_data = self.db_controller.get_categories(self.user_id, category_type)
        
        self.categories_map.clear()
        category_names = [cat['name'] for cat in categories_data]
        for cat in categories_data:
            self.categories_map[cat['name']] = cat['id']
        
        self.category_spinner.values = category_names
        if category_names:
            self.category_spinner.text = category_names[0]
        else:
            self.category_spinner.text = 'No categories found'

    def add_transaction_callback(self, instance):
        """
        Gathers data from the form, validates it, and calls the database
        controller to save the new transaction.
        """
        category_name = self.category_spinner.text
        amount_text = self.amount_input.text
        date_text = self.date_input.text
        note_text = self.note_input.text

        # --- Input Validation ---
        if not amount_text or float(amount_text) <= 0:
            self.show_popup("Input Error", "Please enter a valid amount.")
            return
        if category_name == 'No categories found' or not category_name:
            self.show_popup("Input Error", "Please select a valid category.")
            return

        try:
            amount = float(amount_text)
            category_id = self.categories_map.get(category_name)

            # --- Call to Backend ---
            new_id = self.db_controller.add_transaction(
                user_id=self.user_id, category_id=category_id,
                amount=amount, date=date_text, note=note_text
            )

            # --- Provide Feedback ---
            if new_id:
                self.status_bar.text = f"Success: Transaction (ID: {new_id}) added."
                self.clear_inputs()
            else:
                self.show_popup("Database Error", "Failed to add transaction.")
        
        except ValueError:
            self.show_popup("Input Error", "The amount entered is not a valid number.")
        except Exception as e:
            self.show_popup("An Error Occurred", str(e))

    def export_data_callback(self, instance):
        """
        Exports user transactions to an Excel file in the main project directory.
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_name = f"budget_export_{timestamp}.xlsx"
        
        project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        export_path = os.path.join(project_dir, file_name)
        
        success = self.db_controller.export_transactions_to_excel(
            user_id=self.user_id,
            file_path=export_path
        )
        
        if success:
            self.status_bar.text = f"Success: Data exported to {file_name}"
        else:
            self.show_popup("Export Failed", "Could not export data.\nCheck console for errors.")

    def clear_inputs(self):
        """Resets the input fields to their default state after a successful submission."""
        self.amount_input.text = ""
        self.note_input.text = ""
        self.date_input.text = datetime.now().strftime("%Y-%m-%d %I:%M %p")
        self.type_spinner.text = 'Expense'
        self.status_bar.text = "Ready"

    def show_popup(self, title, text):
        """A helper method to display a simple popup window for errors or info."""
        popup_layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        popup_label = Label(text=text, halign='center')
        close_button = Button(text='Close', size_hint_y=None, height=40)
        
        popup_layout.add_widget(popup_label)
        popup_layout.add_widget(close_button)

        popup = Popup(title=title, content=popup_layout, size_hint=(0.8, 0.4))
        close_button.bind(on_press=popup.dismiss)
        popup.open()


# --- Application Entry Point ---
# This is the standard Python convention to make a script runnable.
if __name__ == '__main__':
    # An instance of our main App class is created, and its run() method is called.
    # This starts the Kivy event loop and builds the UI.
    BudgetApp().run()
