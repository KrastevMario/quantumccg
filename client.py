import asyncio
import websockets
import json
import threading
import os

from kivy.app import App
from kivy.clock import Clock, mainthread
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.gridlayout import GridLayout

KV = "client.kv"

class ClientUI(App):
    def build(self):
        self.root = Builder.load_file(KV)
        self.websocket = None
        self.loop = None
        self.connected = False
        return self.root

    def on_stop(self):
        if self.loop and self.loop.is_running():
            self.loop.call_soon_threadsafe(self.loop.stop)

    def connect_to_server(self):
        if self.connected:
            self.log_message("Already connected.")
            return
        self.log_message("Connecting to server...")
        thread = threading.Thread(target=self.start_async_connection, daemon=True)
        thread.start()

    def start_async_connection(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self.connect_websocket())

    async def connect_websocket(self):
        uri = "ws://localhost:8000/queue"
        try:
            async with websockets.connect(uri) as ws:
                self.websocket = ws
                self.connected = True
                self.update_status("Connected and queued. Waiting for match...")

                async for message in ws:
                    await self.handle_message(message)
        except Exception as e:
            self.log_message(f"Connection error: {e}")
            self.update_status("Disconnected")
            self.connected = False
            self.websocket = None

    async def handle_message(self, message):
        try:
            data = json.loads(message)
            # It's a JSON game state or response
            # Log it nicely
            self.log_message(json.dumps(data, indent=2))
            # If it's a full game state, look for the current player's hand
            if "players" in data and "current_player" in data:
                # Assuming this client is always player 0 for now
                # If you have player identification, adjust accordingly.
                # Here we'll assume the server identifies players by order of connection.
                player_index = 0  # In a real scenario, you might track which player you are.
                player_data = data["players"][player_index]
                cards = player_data.get("hand", [])
                self.update_hand(cards)
        except json.JSONDecodeError:
            # Plain text message
            self.log_message(message)
            if "It's your turn!" in message:
                self.update_status("It's your turn!")
            elif "Match found" in message:
                self.update_status("Match found! Waiting for turn.")

    def send_command(self, cmd):
        if not self.connected or self.websocket is None:
            self.log_message("Not connected to server.")
            return
        asyncio.run_coroutine_threadsafe(self.websocket.send(cmd), self.loop)

    def play_card(self, card_id):
        if card_id.isdigit():
            self.send_command(f"play {card_id}")
        else:
            self.log_message("Invalid card ID.")

    def drag_card(self, card):
        """
        Handles card dragging when a card is pressed.
        """
        # Store the original position of the card for resetting if needed
        card.start_pos = card.pos

        # Enable drag behavior
        card.bind(on_touch_move=self.on_card_move, on_touch_up=self.on_card_drop)

    def on_card_move(self, card, touch):
        """
        Updates the position of the card as it is being dragged.
        """
        if card.collide_point(*touch.pos):
            card.center_x, card.center_y = touch.pos
            return True
        return False

    def on_card_drop(self, card, touch):
        """
        Handles the logic when the card is dropped.
        Checks if the card is over a valid zone.
        """
        # Example: Check if the card is dropped in a monster or spell zone
        root = self.root
        for zone in [root.ids.monster_zone, root.ids.spell_zone]:
            for slot in zone.children:
                if card.collide_widget(slot):
                    print(f"Card {card.text} placed in {slot.id}")
                    card.pos = slot.pos  # Snap card to slot
                    return True

        # Reset the card position if no valid drop zone
        card.pos = card.start_pos
        return False

    @mainthread
    def log_message(self, msg):
        log_label = self.root.ids.log_label
        log_label.text += msg + "\n"

    @mainthread
    def update_status(self, status):
        self.root.ids.status_label.text = status

    @mainthread
    def update_hand(self, cards):
        hand_layout = self.root.ids.hand_layout
        # Clear existing children
        hand_layout.clear_widgets()

        for card in cards:
            card_name = card["name"]
            # Convert card name to a filename. E.g., "Fireball" -> "fireball.png"
            # Ensure images/fireball.png exists
            filename = f"images/{card_name.lower()}.png"
            # Create a layout for the card with image and label
            card_box = BoxLayout(orientation='vertical', size_hint=(1, None), height=200)

            if os.path.exists(filename):
                card_img = Image(source=filename)
            else:
                # If no image found, show a placeholder
                card_img = Image(source="images/placeholder.png")

            card_box.add_widget(card_img)

            # Add a label to show card name and cost
            card_label = Label(text=f"{card_name}\nCost: {card['cost']}")
            card_box.add_widget(card_label)

            hand_layout.add_widget(card_box)


if __name__ == '__main__':
    ClientUI().run()
