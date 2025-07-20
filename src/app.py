# src/app.py

# Kivy imports
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivy.uix.button import Button
from kivy.core.window import Window
from datetime import datetime

# Import our database controller
from database_controller import DatabaseController

# Set a default window size for easier desktop development
Window.size = (400, 550)

class BudgetApp(App):
    """
    This is the main application class that will manage the Kivy UI.
    """

    def build(self):
        """
        This method builds the UI of the application and wires up the initial logic.
        """
        self.title = "My Budget App"
        
        # --- Initialize Backend ---
        # Create an instance of our database controller to interact with the database.
        self.db_controller = DatabaseController()
        # For now, we'll hardcode the user_id. We'll build a login screen later.
        self.user_id = 1 

        # The main layout is a vertical BoxLayout.
        main_layout = BoxLayout(orientation='vertical', padding=15, spacing=10)
        
        # --- Input Form using GridLayout ---
        form_layout = GridLayout(cols=2, spacing=10, size_hint_y=None, height=220)
        
        # 1. Type selection (Income/Expense)
        form_layout.add_widget(Label(text="Type:", font_size='16sp'))
        self.type_spinner = Spinner(
            text='Expense', 
            values=('Expense', 'Income'),
            font_size='16sp'
        )
        # *** BINDING ***: This is the key to making the UI dynamic.
        # We bind the 'text' property of this spinner to our update_categories method.
        # Whenever the spinner's text changes, the method will be called.
        self.type_spinner.bind(text=self.update_categories)
        form_layout.add_widget(self.type_spinner)

        # 2. Category selection
        form_layout.add_widget(Label(text="Category:", font_size='16sp'))
        self.category_spinner = Spinner(
            text='Select Category',
            values=(), # This will be populated by the update_categories method
            font_size='16sp'
        )
        form_layout.add_widget(self.category_spinner)

        # ... (rest of the form widgets are the same) ...
        form_layout.add_widget(Label(text="Amount:", font_size='16sp'))
        self.amount_input = TextInput(multiline=False, input_filter='float', hint_text='0.00', font_size='16sp')
        form_layout.add_widget(self.amount_input)

        form_layout.add_widget(Label(text="Date:", font_size='16sp'))
        self.date_input = TextInput(text=datetime.now().strftime("%Y-%m-%d"), multiline=False, font_size='16sp')
        form_layout.add_widget(self.date_input)

        form_layout.add_widget(Label(text="Note:", font_size='16sp'))
        self.note_input = TextInput(multiline=False, hint_text='Optional description', font_size='16sp')
        form_layout.add_widget(self.note_input)

        main_layout.add_widget(form_layout)
        
        # --- Action Buttons ---
        button_layout = BoxLayout(size_hint_y=None, height=50, spacing=10)
        add_button = Button(text="Add Transaction", font_size='18sp')
        export_button = Button(text="Export Data", font_size='18sp')
        button_layout.add_widget(add_button)
        button_layout.add_widget(export_button)
        main_layout.add_widget(button_layout)

        # --- Transaction List (Placeholder) ---
        main_layout.add_widget(Label(text="Recent transactions will appear here...", size_hint_y=1.0))
        
        # --- Initial Data Load ---
        # Call the update method once at the start to populate the initial categories.
        self.update_categories(self.type_spinner, self.type_spinner.text)
        
        return main_layout

    def update_categories(self, spinner, text):
        """
        This method is called whenever the 'Type' spinner changes.
        It fetches the correct categories from the database and updates the 'Category' spinner.
        """
        print(f"Type changed to: {text}. Updating categories...")
        category_type = text.lower() # Convert 'Expense'/'Income' to 'expense'/'income'
        
        # Fetch categories from the database using our controller
        categories_data = self.db_controller.get_categories(self.user_id, category_type)
        
        # Extract just the names to display in the spinner
        category_names = [cat['name'] for cat in categories_data]
        
        # Update the values of the category spinner
        self.category_spinner.values = category_names
        
        # Set the default text of the category spinner
        if category_names:
            self.category_spinner.text = category_names[0]
        else:
            self.category_spinner.text = 'No categories found'

# This is the standard entry point for running the application.
if __name__ == '__main__':
    BudgetApp().run()
