class GameManager:
    def __init__(self, player1, player2):
        self.player1 = player1
        self.player2 = player2
        self.turn = 0
        self.board = {"player1": [], "player2": []}

    def play_turn(self, player, card_id):
        # Simplified logic for playing a card
        card = self.get_card(card_id)
        if player.mana >= card["cost"]:
            player.mana -= card["cost"]
            self.board[f"player{player.id}"].append(card)
            return {"status": "success", "message": "Card played!"}
        return {"status": "error", "message": "Not enough mana!"}

    def get_card(self, card_id):
        # Placeholder for fetching card data
        return {"id": card_id, "name": "Fireball", "cost": 2, "effect": "deal 5 damage"}

