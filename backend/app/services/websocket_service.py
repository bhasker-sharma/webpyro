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
        """
        Accept a new WebSocket connection
        """
        try:
            # Step 1: Accept the connection (handshake)
            await websocket.accept()
            # Step 2: Add to our list of active connections
            self.active_connections.append(websocket)
            client_info = f"{websocket.client.host}:{websocket.client.port}" if websocket.client else "Unknown"
            logger.info(f"New WebSocket client {client_info} connected. Total clients: {len(self.active_connections)}")
        except Exception as e:
            logger.error(f"Error accepting WebSocket connection: {e}", exc_info=True)
            raise

    async def disconnect(self, websocket: WebSocket):
        """
        Remove a WebSocket connection
        """
        try:
            # Remove from our list of active connections
            if websocket in self.active_connections:
                self.active_connections.remove(websocket)
                client_info = f"{websocket.client.host}:{websocket.client.port}" if websocket.client else "Unknown"
                logger.info(f"WebSocket client {client_info} disconnected. Remaining clients: {len(self.active_connections)}")
            else:
                logger.warning("Attempted to disconnect a WebSocket that was not in active connections")
        except Exception as e:
            logger.error(f"Error during WebSocket disconnect: {e}", exc_info=True)
    
    async def broadcast(self, message: dict):
        """
        Broadcast a message to all connected WebSocket clients
        """
        if not self.active_connections:
            # Don't log "no clients" on every broadcast (too verbose)
            return

        # Keep track of dead connections to remove
        dead_connections = []
        successful_sends = 0

        # Loop through all connected clients
        for connection in self.active_connections:
            try:
                # Try to send the message
                await connection.send_json(message)
                successful_sends += 1

            except Exception as e:
                # Connection is dead (user closed tab, network issue, etc.)
                client_info = f"{connection.client.host}:{connection.client.port}" if connection.client else "Unknown"
                logger.warning(f"Failed to send to WebSocket client {client_info}: {type(e).__name__}: {e}")
                dead_connections.append(connection)

        # Remove dead connections from the list
        for dead_conn in dead_connections:
            await self.disconnect(dead_conn)

        # Only log if there were failures (don't log every successful broadcast)
        if dead_connections:
            logger.info(f"Broadcast: {successful_sends} successful, {len(dead_connections)} failed")


# ============================================================================
# CREATE SINGLETON INSTANCE
# ============================================================================

websocket_manager = ConnectionManager()

