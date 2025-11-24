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
    """
    WebSocket endpoint for real-time temperature updates
    """
    client_info = f"{websocket.client.host}:{websocket.client.port}" if websocket.client else "Unknown"

    # Step 1: Connect the client
    logger.info(f"WebSocket connection request from {client_info}")
    try:
        await websocket_manager.connect(websocket)
        logger.info(f"WebSocket client {client_info} connected successfully")
    except Exception as e:
        logger.error(f"Failed to establish WebSocket connection with {client_info}: {e}", exc_info=True)
        return

    try:
        # Keep connection alive and listen for client messages
        while True:
            data = await websocket.receive_text()
            logger.debug(f"Received message from WebSocket client {client_info}: {data}")

    except WebSocketDisconnect:
        # Network connection lost (normal disconnect)
        logger.info(f"WebSocket client {client_info} disconnected normally")
        await websocket_manager.disconnect(websocket)

    except Exception as e:
        # Handle any other errors
        logger.error(f"WebSocket error with client {client_info}: {type(e).__name__}: {e}", exc_info=True)
        try:
            await websocket_manager.disconnect(websocket)
        except Exception as disconnect_error:
            logger.error(f"Error during WebSocket cleanup for {client_info}: {disconnect_error}", exc_info=True)