import socketio
import asyncio
import time

sio = socketio.AsyncClient()

@sio.event
async def connect():
    print("Connected to server!", flush=True)
    
    # 1. Start Typing
    print("Simulating typing start...", flush=True)
    await sio.emit('start_typing')
    await asyncio.sleep(2)
    
    # 2. Stop Typing
    print("Simulating typing stop...", flush=True)
    await sio.emit('stop_typing')
    await asyncio.sleep(2)

    # 3. Toggle Listening
    print("Simulating voice toggle off...", flush=True)
    await sio.emit('toggle_listening', {'active': False})
    await asyncio.sleep(2)

    print("Simulating voice toggle on...", flush=True)
    await sio.emit('toggle_listening', {'active': True})
    await asyncio.sleep(2)
    
    print("Test Complete", flush=True)
    await sio.disconnect()

async def main():
    try:
        await sio.connect('http://localhost:8000')
        await sio.wait()
    except Exception as e:
        print(f"Connection failed: {e}", flush=True)

if __name__ == '__main__':
    asyncio.run(main())
