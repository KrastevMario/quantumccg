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
from kivy.uix.floatlayout import FloatLayout
from kivy.graphics import Color, Rectangle
from kivy.core.window import Window
import os  # For checking file existence


KV = "client.kv"

class UICard(BoxLayout):
    """Custom Widget for displaying a card."""
    card_image = StringProperty("")
    card_title = StringProperty("")
    card_description = StringProperty("")


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
                player_board = player_data.get("board", [])
                enemy_board = enemy_data.get("board", [])
                self.update_hand(cards)
                print("I AM BEFORE UPDATE ARENA")
                self.update_arena(player_board, enemy_board)
                print("I AM AFTER UPDATED_ARENA")
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

    #update UI status_label with the current status that relates to the player state in the server
    @mainthread
    def update_status(self, status):
        self.root.ids.status_label.text = status

    @mainthread
    def update_hand(self, cards):
        hand_layout = self.root.ids.hand_layout
        hand_layout.clear_widgets()  # Clear previous widgets

        for card in cards:
            # Create card container
            card_box = FloatLayout(size_hint=(None, None), size=(Window.width * 0.1, Window.height * 0.2))

            # Background Image
            background_image = Image(
                source="images/card_background.png",  # Background image for the card
                allow_stretch=True,
                keep_ratio=False,
                size_hint=(1, 1),
                pos_hint={"x": 0, "y": 0}
            )
            card_box.add_widget(background_image)

            # Card Image
            card_img_src = f"images/{card['name'].lower()}.png" if os.path.exists(f"images/{card['name'].lower()}.png") else "images/placeholder.png"
            card_image = Image(
                source=card_img_src,
                allow_stretch=True,
                size_hint=(1, 0.6),
                pos_hint={"x": 0, "y": 0.2}
            )
            card_box.add_widget(card_image)

            # Title Label
            card_title = Label(
                text=card['name'],
                font_name='fonts/stats_font.ttf',
                font_size=Window.height * 0.02,
                bold=True,
                color=(1, 1, 0, 1),  # Yellow text
                halign='center',
                size_hint=(1, None),
                height=Window.height * 0.04,
                pos_hint={"x": 0, "y": 0.8}
            )
            card_box.add_widget(card_title)

            # Description Label
            card_description = Label(
                text=f"Cost: {card['cost']}\nEffect: {card['effect']}",
                font_name='fonts/stats_font.ttf',
                font_size=Window.height * 0.015,
                halign='center',
                valign='middle',
                text_size=(card_box.size[0], None),
                color=(1, 1, 1, 1),  # White text
                size_hint=(1, None),
                height=Window.height * 0.05,
                pos_hint={"x": 0, "y": 0}
            )
            card_box.add_widget(card_description)

            # Add card to hand layout
            hand_layout.add_widget(card_box)

    #player stats like hp, mana, shield
    @mainthread
    def update_player_stats(self, player_hp, player_mana, player_shield, enemy_hp, enemy_mana, enemy_shield):
        self.root.ids.health_label.text = f"Your HP: {player_hp}"
        self.root.ids.mana_label.text = f"Your Mana: {player_mana}"
        self.root.ids.shield_label.text = f"Your Shield: {player_shield}"

        self.root.ids.enemy_health_label.text = f"Enemy HP: {enemy_hp}"
        self.root.ids.enemy_mana_label.text = f"Enemy Mana: {enemy_mana}"
        self.root.ids.enemy_shield_label.text = f"Enemy Shield: {enemy_shield}"

    @mainthread
    def update_arena(self, player_monsters, enemy_monsters):
        arena_layout = self.root.ids.arena_layout
        arena_layout.clear_widgets()  # Clear previous widgets

        # Add enemy monsters (top row)
        for monster in enemy_monsters:
            monster_card = self.create_monster_card(monster)
            arena_layout.add_widget(monster_card)

        # Add player monsters (bottom row)
        for monster in player_monsters:
            monster_card = self.create_monster_card(monster)
            arena_layout.add_widget(monster_card)

    def create_monster_card(self, monster):
        if monster:
            card_box = FloatLayout(size_hint=(None, None), size=(Window.width * 0.1, Window.height * 0.2))

            # Background
            with card_box.canvas.before:
                Color(rgba=(1, 1, 1, 1))  # Background color
                Rectangle(size=card_box.size, pos=card_box.pos, source="images/card_background.png")

            # Monster Image
            card_img_src = f"images/{monster['name'].lower()}.png" if os.path.exists(f"images/{monster['name'].lower()}.png") else "images/placeholder.png"
            card_image = Image(
                source=card_img_src,
                allow_stretch=True,
                size_hint=(1, 0.6),
                pos_hint={"x": 0, "y": 0.2}
            )
            card_box.add_widget(card_image)

            # Monster Name
            monster_title = Label(
                text=monster['name'],
                font_name='fonts/stats_font.ttf',
                font_size=Window.height * 0.02,
                bold=True,
                color=(1, 1, 0, 1),
                halign='center',
                size_hint=(1, None),
                height=Window.height * 0.04,
                pos_hint={"x": 0, "y": 0.8}
            )
            card_box.add_widget(monster_title)

            # Monster Stats
            monster_stats = Label(
                text=f"HP: {monster['health']}\nATK: {monster['attack']}\nDEF: {monster['shield']}",
                font_name='fonts/stats_font.ttf',
                font_size=Window.height * 0.015,
                halign='center',
                valign='middle',
                text_size=(card_box.size[0], None),
                color=(1, 1, 1, 1),
                size_hint=(1, None),
                height=Window.height * 0.05,
                pos_hint={"x": 0, "y": 0}
            )
            card_box.add_widget(monster_stats)

            return card_box
        else:
            # Empty Slot
            return FloatLayout(size_hint=(None, None), size=(Window.width * 0.1, Window.height * 0.2))


if __name__ == '__main__':
    ClientUI().run()
