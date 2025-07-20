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

# Set a default window size for easier desktop development
Window.size = (400, 550)

class BudgetApp(App):
    """
    This is the main application class that will manage the Kivy UI.
    """

    def build(self):
        """
        This method builds the UI of the application, including input fields and buttons.
        """
        self.title = "My Budget App"
        
        # The main layout is a vertical BoxLayout. Widgets are added from top to bottom.
        main_layout = BoxLayout(orientation='vertical', padding=15, spacing=10)
        
        # --- Input Form using GridLayout ---
        # A GridLayout is perfect for forms, arranging widgets in a table-like grid.
        form_layout = GridLayout(cols=2, spacing=10, size_hint_y=None, height=220)
        
        # 1. Type selection (Income/Expense)
        form_layout.add_widget(Label(text="Type:", font_size='16sp'))
        # A Spinner is Kivy's version of a dropdown menu.
        self.type_spinner = Spinner(
            text='Expense', 
            values=('Expense', 'Income'),
            font_size='16sp'
        )
        form_layout.add_widget(self.type_spinner)

        # 2. Category selection
        form_layout.add_widget(Label(text="Category:", font_size='16sp'))
        self.category_spinner = Spinner(
            text='Select Category',
            values=(), # We will populate this dynamically later
            font_size='16sp'
        )
        form_layout.add_widget(self.category_spinner)

        # 3. Amount input
        form_layout.add_widget(Label(text="Amount:", font_size='16sp'))
        self.amount_input = TextInput(
            multiline=False, 
            input_filter='float', # Only allows numbers and a decimal point
            hint_text='0.00',
            font_size='16sp'
        )
        form_layout.add_widget(self.amount_input)

        # 4. Date input
        form_layout.add_widget(Label(text="Date:", font_size='16sp'))
        self.date_input = TextInput(
            text=datetime.now().strftime("%Y-%m-%d"), # Default to today's date
            multiline=False,
            font_size='16sp'
        )
        form_layout.add_widget(self.date_input)

        # 5. Note input
        form_layout.add_widget(Label(text="Note:", font_size='16sp'))
        self.note_input = TextInput(
            multiline=False, 
            hint_text='Optional description',
            font_size='16sp'
        )
        form_layout.add_widget(self.note_input)

        # Add the form grid to the main vertical layout
        main_layout.add_widget(form_layout)
        
        # --- Action Buttons ---
        # A horizontal BoxLayout for the buttons
        button_layout = BoxLayout(size_hint_y=None, height=50, spacing=10)
        
        add_button = Button(text="Add Transaction", font_size='18sp')
        export_button = Button(text="Export Data", font_size='18sp')
        
        button_layout.add_widget(add_button)
        button_layout.add_widget(export_button)
        
        main_layout.add_widget(button_layout)

        # --- Transaction List (Placeholder) ---
        # This label fills the remaining space. We'll replace it with a real list later.
        main_layout.add_widget(Label(
            text="Recent transactions will appear here...",
            size_hint_y=1.0 # Allow this widget to stretch vertically
        ))
        
        return main_layout

# This is the standard entry point for running the application.
if __name__ == '__main__':
    BudgetApp().run()
