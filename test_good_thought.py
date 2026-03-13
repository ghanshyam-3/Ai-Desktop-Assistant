import socketio
import asyncio
import time

sio = socketio.AsyncClient()

@sio.event
async def connect():
    print("Connected to server!", flush=True)
    # Send the command
    await sio.emit('text_command', {'text': 'Tell me a good thought'})

@sio.event
async def chat(data):
    print(f"Chat received: {data}", flush=True)
    if data.get('role') == 'ai':
        print("Test Passed: Received AI response", flush=True)
        await sio.disconnect()

@sio.event
async def disconnect():
    print("Disconnected", flush=True)

async def main():
    print("Attempting to connect...", flush=True)
    try:
        await sio.connect('http://localhost:8000', wait_timeout=10)
        await sio.wait()
    except Exception as e:
        print(f"Connection failed: {e}", flush=True)

if __name__ == '__main__':
    asyncio.run(main())
