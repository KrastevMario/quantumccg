import websockets
import asyncio

async def game_client():
    uri = "ws://localhost:8000/game"
    async with websockets.connect(uri) as websocket:
        print("Connected to game server!")

        while True:
            command = input("Enter command (play/end): ")
            await websocket.send(command)
            response = await websocket.recv()
            print(f"Server: {response}")

asyncio.run(game_client())
