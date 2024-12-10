import asyncio
import json

class Card:
    def __init__(self, id, name, health, attack, mana, shield, type, cost, effect):
        self.id = id
        self.name = name
        self.health = health
        self.attack = attack
        self.mana = mana
        self.shield = shield
        self.type = type
        self.cost = cost
        self.effect = effect

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "health": self.health,
            "attack": self.attack,
            "mana": self.mana,
            "shield": self.shield,
            "type": self.type,
            "cost": self.cost,
            "effect": self.effect,
        }

class Player:
    def __init__(self, websocket):
        self.websocket = websocket
        self.name = "Player"
        self.health = 20
        self.mana = 10
        self.shield = 0
        self.deck = [
            Card(1, "Fireball", 0, 0, 0, 0, "Spell", 3, "deal 5 damage"),
            Card(2, "Monster1", 20, 139, 0, 0, "Monster", 2, "self gain 3 shield"),
            Card(3, "Shield", 0, 0, 0, 0, "Spell", 2, "gain 3 shield"),
        ]
        self.hand = []
        self.board = []

    def draw_card(self):
        if self.deck:
            card = self.deck.pop(0)
            self.hand.append(card)
            return card
        return None

    def play_card(self, card_id):
        card = next((c for c in self.hand if c.id == card_id), None)
        if card and self.mana >= card.cost:
            self.hand.remove(card)
            self.mana -= card.cost
            return card
        return None


class CardEffects:
    @staticmethod
    def apply_effect(game, player, target, effect):
        if effect == "deal 5 damage":
            target.health -= 5
        elif effect == "gain 3 shield":
            player.shield += 3
        # Add more effects as needed.


class Game:
    TURN_DURATION = 20

    def __init__(self, player1, player2):
        self.players = [player1, player2]
        self.current_turn = 0
        self.active = True
        self.turn_ended_early = False

    async def start_game(self):
        for p in self.players:
            p.draw_card()
            p.draw_card()
        asyncio.create_task(self.turn_loop())

    async def turn_loop(self):
        while self.active:
            current_p = self.current_player()
            await self.safe_send(current_p.websocket, "It's your turn!")
            await self.send_game_state()

            self.turn_ended_early = False
            total_wait = 0
            while total_wait < self.TURN_DURATION and not self.turn_ended_early:
                await asyncio.sleep(0.5)
                total_wait += 0.5

            if not self.turn_ended_early:
                self.end_turn()

    def end_turn(self):
        self.turn_ended_early = True
        self.current_turn = (self.current_turn + 1) % len(self.players)

    def current_player(self):
        return self.players[self.current_turn]

    def opponent_player(self):
        return self.players[1 - self.current_turn]

    async def send_game_state(self):
        state = {
            "current_player": self.players.index(self.current_player()),
            "players": [
                {
                    "health": p.health,
                    "mana": p.mana,
                    "shield": p.shield,
                    "hand": [c.to_dict() for c in p.hand],  # Serialize cards
                    "board": [c.to_dict() for c in p.board] if p.board else []  # Serialize board cards
                }
                for p in self.players
            ]
        }
        import json
        msg = json.dumps(state)  # Now JSON serializable
        for p in self.players:
            await self.safe_send(p.websocket, msg)


    async def safe_send(self, websocket, message):
        try:
            await websocket.send_text(message)
        except:
            pass


class GameManager:
    def __init__(self):
        self.games = []
        self.player_game_map = {}

    def register_game(self, game):
        self.games.append(game)

    def process_command(self, player, command):
        game = self.find_game_for_player(player)
        if not game:
            return "You are not in a game."

        parts = command.split()
        cmd = parts[0]

        actions_require_turn = ["draw", "play", "end"]
        if cmd in actions_require_turn and player != game.current_player():
            return "It's not your turn!"

        if cmd == "draw":
            card = player.draw_card()
            if card:
                return f"You drew {card.name}!"
            return "No more cards in the deck!"
        elif cmd == "play":
            if len(parts) < 2:
                return "Specify a card id: 'play <card_id>'"
            card_id = int(parts[1])
            card = player.play_card(card_id)
            if card:
                current_p = game.current_player()
                opponent = game.opponent_player()
                if card.type.lower() == "monster":
                    current_p.board.append(card)
                if "deal" in card.effect:
                    CardEffects.apply_effect(game, player, opponent, card.effect)
                if "self" in card.effect:
                    CardEffects.apply_effect(game, card, opponent, card.effect)
                else:
                    CardEffects.apply_effect(game, player, player, card.effect)
                game.end_turn()
                print("You played {card.name}! Effect: {card.effect}")
                return f"You played {card.name}! Effect: {card.effect}"
            return "Invalid card or insufficient mana."
        elif cmd == "end":
            if player == game.current_player():
                game.end_turn()
                return "Turn ended."
            else:
                return "It's not your turn!"

        elif cmd == "stats":
            return f"Health: {player.health}, Mana: {player.mana}, Shield: {player.shield}"
        else:
            return "Unknown command. Use 'draw', 'play <id>', 'end', or 'stats'."

    def find_game_for_player(self, player):
        for g in self.games:
            if player in g.players:
                return g
        return None
