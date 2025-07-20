# src/app.py

# Kivy imports
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivy.uix.button import Button
from kivy.uix.popup import Popup
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
        self.db_controller = DatabaseController()
        self.user_id = 1 # Hardcoded user_id for now
        self.categories_map = {} # To map category names to their IDs

        # --- UI Layout ---
        main_layout = BoxLayout(orientation='vertical', padding=15, spacing=10)
        form_layout = GridLayout(cols=2, spacing=10, size_hint_y=None, height=220)
        
        # 1. Type selection
        form_layout.add_widget(Label(text="Type:", font_size='16sp'))
        self.type_spinner = Spinner(text='Expense', values=('Expense', 'Income'), font_size='16sp')
        self.type_spinner.bind(text=self.update_categories)
        form_layout.add_widget(self.type_spinner)

        # 2. Category selection
        form_layout.add_widget(Label(text="Category:", font_size='16sp'))
        self.category_spinner = Spinner(text='Select Category', values=(), font_size='16sp')
        form_layout.add_widget(self.category_spinner)

        # 3. Amount input
        form_layout.add_widget(Label(text="Amount:", font_size='16sp'))
        self.amount_input = TextInput(multiline=False, input_filter='float', hint_text='0.00', font_size='16sp')
        form_layout.add_widget(self.amount_input)

        # 4. Date input
        form_layout.add_widget(Label(text="Date:", font_size='16sp'))
        self.date_input = TextInput(text=datetime.now().strftime("%Y-%m-%d"), multiline=False, font_size='16sp')
        form_layout.add_widget(self.date_input)

        # 5. Note input
        form_layout.add_widget(Label(text="Note:", font_size='16sp'))
        self.note_input = TextInput(multiline=False, hint_text='Optional description', font_size='16sp')
        form_layout.add_widget(self.note_input)

        main_layout.add_widget(form_layout)
        
        # --- Action Buttons ---
        button_layout = BoxLayout(size_hint_y=None, height=50, spacing=10)
        
        add_button = Button(text="Add Transaction", font_size='18sp')
        # *** BINDING ***: Connect the button's 'on_press' event to our new method.
        add_button.bind(on_press=self.add_transaction_callback)
        
        export_button = Button(text="Export Data", font_size='18sp')
        
        button_layout.add_widget(add_button)
        button_layout.add_widget(export_button)
        main_layout.add_widget(button_layout)

        # --- Transaction List (Placeholder) ---
        main_layout.add_widget(Label(text="Recent transactions will appear here...", size_hint_y=1.0))
        
        # --- Initial Data Load ---
        self.update_categories(self.type_spinner, self.type_spinner.text)
        
        return main_layout

    def update_categories(self, spinner, text):
        """
        Fetches categories from the DB and updates the category spinner.
        Also updates the categories_map to store IDs.
        """
        category_type = text.lower()
        categories_data = self.db_controller.get_categories(self.user_id, category_type)
        
        # Clear the old map and prepare names for the spinner
        self.categories_map.clear()
        category_names = []
        for cat in categories_data:
            self.categories_map[cat['name']] = cat['id']
            category_names.append(cat['name'])
        
        self.category_spinner.values = category_names
        if category_names:
            self.category_spinner.text = category_names[0]
        else:
            self.category_spinner.text = 'No categories found'

    def add_transaction_callback(self, instance):
        """
        This method is called when the 'Add Transaction' button is pressed.
        It validates input, saves the data, and provides user feedback.
        """
        # 1. Gather data from UI
        category_name = self.category_spinner.text
        amount_text = self.amount_input.text
        date_text = self.date_input.text
        note_text = self.note_input.text

        # 2. Validate input
        if not amount_text or float(amount_text) <= 0:
            self.show_popup("Input Error", "Please enter a valid amount.")
            return
        if category_name == 'No categories found' or not category_name:
            self.show_popup("Input Error", "Please select a valid category.")
            return

        # 3. Process data
        try:
            amount = float(amount_text)
            category_id = self.categories_map.get(category_name)

            # 4. Call the database controller
            new_id = self.db_controller.add_transaction(
                user_id=self.user_id,
                category_id=category_id,
                amount=amount,
                date=date_text,
                note=note_text
            )

            # 5. Provide feedback
            if new_id:
                self.show_popup("Success", f"Transaction added successfully (ID: {new_id}).")
                self.clear_inputs()
            else:
                self.show_popup("Database Error", "Failed to add transaction.")
        
        except ValueError:
            self.show_popup("Input Error", "The amount entered is not a valid number.")
        except Exception as e:
            self.show_popup("An Error Occurred", str(e))

    def clear_inputs(self):
        """Resets the input fields to their default state."""
        self.amount_input.text = ""
        self.note_input.text = ""
        self.date_input.text = datetime.now().strftime("%Y-%m-%d")
        # Optionally reset spinners to default
        self.type_spinner.text = 'Expense'

    def show_popup(self, title, text):
        """Displays a simple popup window with a title and message."""
        popup_layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        popup_label = Label(text=text)
        close_button = Button(text='Close', size_hint_y=None, height=40)
        
        popup_layout.add_widget(popup_label)
        popup_layout.add_widget(close_button)

        popup = Popup(title=title, content=popup_layout, size_hint=(0.8, 0.4))
        close_button.bind(on_press=popup.dismiss)
        popup.open()


if __name__ == '__main__':
    BudgetApp().run()
