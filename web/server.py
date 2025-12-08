import sys
import os
import asyncio
import threading
import queue
import json
import logging
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.llm.gui.agent import GUIAgent
from core.llm.code.agent import CodeAgent

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("WebServer")

app = FastAPI()

# Mount static files
app.mount("/static", StaticFiles(directory="web/static"), name="static")

@app.get("/")
async def get():
    return FileResponse('web/index.html')

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

manager = ConnectionManager()

def run_agent_thread(agent, task_desc, msg_from_client, msg_to_client):
    try:
        agent.task(task_desc, msg_from_client, msg_to_client)
    except Exception as e:
        logger.error(f"Agent Task Error: {e}")
        msg_to_client.put({"type": "error", "content": str(e)})

@app.websocket("/ws/{agent_type}")
async def websocket_endpoint(websocket: WebSocket, agent_type: str):
    await manager.connect(websocket)
    
    agent = None
    if agent_type == "gui":
        agent = GUIAgent()
    elif agent_type == "code":
        agent = CodeAgent()
    
    msg_from_client = queue.Queue()
    msg_to_client = queue.Queue()
    
    agent_thread = None
    stop_event = threading.Event()

    try:
        while True:
            # Check for messages from client (non-blocking usually, but here we await)
            # We need a way to forward client messages to agent's input queue
            # AND forward agent's output queue to client.
            # This requires a dual-loop or async handling.
            
            # Simplified approach: Use a very short timeout for receiving client messages
            # But we can't block the loop listening to the queue.
            
            # Better approach: 
            # 1. Start a background task to push msg_to_client -> websocket
            # 2. Main loop waits for websocket -> msg_from_client
            
            # Wait for initiation
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get("action") == "start":
                task_desc = message.get("task")
                if not agent_thread or not agent_thread.is_alive():
                    agent_thread = threading.Thread(
                        target=run_agent_thread, 
                        args=(agent, task_desc, msg_from_client, msg_to_client)
                    )
                    agent_thread.daemon = True
                    agent_thread.start()
                    
                    # Start the output forwarder
                    asyncio.create_task(forward_output(websocket, msg_to_client))
            
            elif message.get("action") == "input":
                # Forward user input/permission to agent
                # CodeAgent expects specific format for permissions
                content = message.get("content")
                msg_from_client.put({
                    "name": "CodeAgent" if agent_type == "code" else "GUIAgent",
                    "type": "request",
                    "content": content
                })
                
            elif message.get("action") == "stop":
                msg_from_client.put({
                    "name": "CodeAgent" if agent_type == "code" else "GUIAgent",
                    "type": "request",
                    "content": "stop_agent"
                })

    except WebSocketDisconnect:
        manager.disconnect(websocket)
        # Try to stop agent if possible
        if agent:
            msg_from_client.put({"name": "System", "type": "request", "content": "stop_agent"})

async def forward_output(websocket: WebSocket, q: queue.Queue):
    """Continuously reads from the sync queue and sends to websocket"""
    while True:
        try:
            # Non-blocking get from queue
            try:
                msg = q.get_nowait()
                await websocket.send_json(msg)
            except queue.Empty:
                await asyncio.sleep(0.1) # Yield control
        except Exception as e:
            logger.error(f"Error forwarding output: {e}")
            break
            
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
