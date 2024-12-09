from kivy.uix.boxlayout import BoxLayout
from kivy.properties import StringProperty

class UICard(BoxLayout):
    """Kivy Widget for displaying a card visually."""
    card_image = StringProperty("")
    card_description = StringProperty("")
