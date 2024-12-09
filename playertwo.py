import asyncio
import websockets

async def player_two():
    uri = "ws://localhost:8000/queue"
    async with websockets.connect(uri) as websocket:
        # Wait for messages from the server
        msg = await websocket.recv()
        print("Player 2 received:", msg)

        # Next message should be "Match found!"
        msg = await websocket.recv()
        print("Player 2 received:", msg)

        # Wait for game messages
        while True:
            msg = await websocket.recv()
            print("Player 2 received:", msg)
            # Player 2 can also send commands, e.g. "stats"
            await websocket.send("stats")
            stats_msg = await websocket.recv()
            print("Player 2 received:", stats_msg)
            break

asyncio.run(player_two())
