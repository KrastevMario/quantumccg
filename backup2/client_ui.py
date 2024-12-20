import asyncio
import websockets
import json
import threading
import os
from datetime import datetime

from kivy.app import App
from kivy.clock import Clock, mainthread
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.properties import StringProperty

KV = "client.kv"

class UICard(BoxLayout):
    """Kivy Widget for displaying a card visually."""
    card_image = StringProperty("")  # Path to the card image
    card_description = StringProperty("")  # Card description text

class ClientUI(App):
    def build(self):
        self.root = Builder.load_file(KV)
        self.websocket = None
        self.loop = None
        self.connected = False
        self.log_data = []
        # Initialize player_index as None until we know which player this client is.
        self.player_index = None
        return self.root

    def on_stop(self):
        if self.loop and self.loop.is_running():
            self.loop.call_soon_threadsafe(self.loop.stop)

    def connect_to_server(self):
        if self.connected:
            self.add_log("Already connected.")
            return
        self.add_log("Connecting to server...")
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
            self.add_log(f"Connection error: {e}")
            self.update_status("Disconnected")
            self.connected = False
            self.websocket = None

    async def handle_message(self, message):
        if "You are Player 1" in message:
            self.player_index = 0
            self.add_log("You are Player 1.")
        elif "You are Player 2" in message:
            self.player_index = 1
            self.add_log("You are Player 2.")

        try:
            data = json.loads(message)
            self.add_log("Game State Update:")

            if "players" in data and "current_player" in data and self.player_index is not None:
                player_data = data["players"][self.player_index]
                enemy_data = data["players"][1 - self.player_index]

                # Update stats and hand as before
                health = player_data["health"]
                mana = player_data["mana"]
                shield = player_data["shield"]
                self.update_player_stats(
                    health, mana, shield,
                    enemy_data["health"],
                    enemy_data["mana"],
                    enemy_data["shield"]
                )

                cards = player_data.get("hand", [])
                self.update_hand(cards)

                # Check whose turn it is
                if data["current_player"] == self.player_index:
                    self.update_status("It's your turn!")
                else:
                    self.update_status("Wait for your turn...")

        except json.JSONDecodeError:
            self.add_log(message)

    def send_command(self, cmd):
        if not self.connected or self.websocket is None:
            self.add_log("Not connected to server.")
            return
        asyncio.run_coroutine_threadsafe(self.websocket.send(cmd), self.loop)

    def play_card(self, card_id):
        if card_id.isdigit():
            self.send_command(f"play {card_id}")
        else:
            self.add_log("Invalid card ID.")

    @mainthread
    def add_log(self, msg):
        timestamp = datetime.now().strftime("[%H:%M:%S]")
        self.log_data.insert(0, {"text": f"{timestamp} {msg}"})
        #self.root.ids.log_view.data = self.log_data[:]

    @mainthread
    def update_status(self, status):
        self.root.ids.status_label.text = status

    @mainthread
    def update_hand(self, cards):
        hand_layout = self.root.ids.hand_layout
        hand_layout.clear_widgets()

        for card in cards:
            # Create card widget
            card_box = BoxLayout(orientation="vertical", size_hint=(None, None), size=(150, 200))
            card_img_src = f"images/{card['name'].lower()}.png" if os.path.exists(f"images/{card['name'].lower()}.png") else "images/placeholder.png"
            
            card_img = Image(source=card_img_src, allow_stretch=True, size_hint=(1, 0.8))
            card_label = Label(
                text=f"{card['name']}\nCost: {card['cost']}\nEffect: {card['effect']}",
                halign="center",
                valign="middle",
                size_hint=(1, 0.2)
            )
            card_label.bind(size=card_label.setter("text_size"))

            card_box.add_widget(card_img)
            card_box.add_widget(card_label)

            # Add card to hand layout
            hand_layout.add_widget(card_box)


    @mainthread
    def update_player_stats(self, player_hp, player_mana, player_shield, enemy_hp, enemy_mana, enemy_shield):
        self.root.ids.health_label.text = f"Your HP: {player_hp}"
        self.root.ids.mana_label.text = f"Your Mana: {player_mana}"
        self.root.ids.shield_label.text = f"Your Shield: {player_shield}"

        self.root.ids.enemy_health_label.text = f"Enemy HP: {enemy_hp}"
        self.root.ids.enemy_mana_label.text = f"Enemy Mana: {enemy_mana}"
        self.root.ids.enemy_shield_label.text = f"Enemy Shield: {enemy_shield}"

if __name__ == '__main__':
    ClientUI().run()
