"""
WebSocket Service
Manages WebSocket connections and broadcasts real-time temperature data
"""

import logging
from typing import List
from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        logger.info("WebSocket ConnectionManager initialized")
    
    async def connect(self, websocket: WebSocket):
        # Step 1: Accept the connection (handshake)
        await websocket.accept()
        # Step 2: Add to our list of active connections
        self.active_connections.append(websocket)
        logger.info(f" New WebSocket client connected. Total clients: {len(self.active_connections)}")
    
    async def disconnect(self, websocket: WebSocket):
        # Remove from our list of active connections
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"❌ WebSocket client disconnected. Total clients: {len(self.active_connections)}")
    
    async def broadcast(self, message: dict):
        # Keep track of dead connections to remove
        dead_connections = []
        # Loop through all connected clients
        for connection in self.active_connections:
            try:
                # Try to send the message
                await connection.send_json(message)
       
            except Exception as e:
                # Connection is dead (user closed tab, network issue, etc.)
                logger.warning(f"Failed to send to client: {e}")
                dead_connections.append(connection)
        
        # Remove dead connections from the list
        for dead_conn in dead_connections:
            await self.disconnect(dead_conn)
        
        # Log broadcast info (only if there are active clients)
        if self.active_connections:
            logger.debug(f" Broadcasted to {len(self.active_connections)} client(s)")


# ============================================================================
# CREATE SINGLETON INSTANCE
# ============================================================================

websocket_manager = ConnectionManager()

