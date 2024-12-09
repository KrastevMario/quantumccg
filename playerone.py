import asyncio
import websockets

async def player_one():
    uri = "ws://localhost:8000/queue"
    async with websockets.connect(uri) as websocket:
        # First message from server: "You joined the queue. Waiting for an opponent..."
        msg = await websocket.recv()
        print("Player 1 received:", msg)

        # Wait for match found message
        msg = await websocket.recv()
        print("Player 1 received:", msg)

        # After match found, a game should start.
        # The server may send "It's your turn!" or game state updates.
        while True:
            msg = await websocket.recv()
            print("Player 1 received:", msg)
            # You can send commands to interact:
            # e.g. "draw", "stats", "play 1", "end"
            # Let's try a command:
            await websocket.send("stats")
            print("Player 1 stats request sent")

            # Wait for response
            msg = await websocket.recv()
            print("Player 1 received:", msg)
            break  # Exit after one interaction

asyncio.run(player_one())
