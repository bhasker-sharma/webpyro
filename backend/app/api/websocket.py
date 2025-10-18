"""
WebSocket API Endpoints
Real-time data streaming for temperature readings
"""

import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.services.websocket_service import websocket_manager

logger = logging.getLogger(__name__)

# Create router for WebSocket endpoints
router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    
    # Step 1: Connect the client
    await websocket_manager.connect(websocket)
    
    try:
        while True:
            data = await websocket.receive_text()
            logger.debug(f"Received from client: {data}")
            
    except WebSocketDisconnect:
        # Network connection lost
        logger.info("Client disconnected normally")
        await websocket_manager.disconnect(websocket)
        
    except Exception as e:
        # Handle any other errors
        logger.error(f"WebSocket error: {e}")
        await websocket_manager.disconnect(websocket)