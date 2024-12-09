from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from db_setup import Base, engine
from game_logic import GameManager, Player, Game
import asyncio

app = FastAPI()
Base.metadata.create_all(bind=engine)

connected_players = []
waiting_players = []
active_games = []
game_manager = GameManager()

@app.get("/")
async def root():
    return {"message": "Welcome to the Turn-Based Card Game Server!"}

@app.websocket("/queue")
async def queue_endpoint(websocket: WebSocket):
    await websocket.accept()
    player = Player(websocket)
    connected_players.append(player)

    # Notify the player that they have joined the queue
    await player.websocket.send_text("You joined the queue. Waiting for an opponent...")
    waiting_players.append(player)

    # Attempt to match two players if possible
    if len(waiting_players) >= 2:
        player1 = waiting_players.pop(0)
        player2 = waiting_players.pop(0)

        await player1.websocket.send_text("Match found! You are Player 1.")
        await player2.websocket.send_text("Match found! You are Player 2.")

        # Initialize a new game with the two matched players
        game = Game(player1, player2)
        active_games.append(game)
        game_manager.register_game(game)

        # Start the game's turn loop in a background task
        asyncio.create_task(game.start_game())

    try:
        while True:
            # From the queue_endpoint logic:
            data = await websocket.receive_text()
            response = game_manager.process_command(player, data)
            await websocket.send_text(response)

            game = game_manager.find_game_for_player(player)
            if game:
                cmd = data.split()[0]
                if cmd in ["play", "draw", "end"]:
                    # Send updated state only, no turn messages here
                    await game.send_game_state()


    except WebSocketDisconnect:
        # If the player disconnects, remove them from the connected list
        connected_players.remove(player)
        # If they were still in the waiting queue, remove them from there too
        if player in waiting_players:
            waiting_players.remove(player)
        # No sending messages after disconnect


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    # A test endpoint for single player interactions if needed
    await websocket.accept()
    player = Player(websocket)
    connected_players.append(player)
    await websocket.send_text("Connected. Use 'draw', 'stats', 'play <id>', 'end'. Not queued.")

    try:
        while True:
            data = await websocket.receive_text()
            response = game_manager.process_command(player, data)
            await websocket.send_text(response)
    except WebSocketDisconnect:
        connected_players.remove(player)
