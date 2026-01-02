"""WebSocket service for real-time notifications."""
import json
import logging
from typing import Dict, Set
from fastapi import WebSocket
from datetime import datetime

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections for real-time notifications."""
    
    def __init__(self):
        # Store active connections: {admin_id: {websocket1, websocket2, ...}}
        self.active_connections: Dict[int, Set[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, admin_id: int):
        """Accept a new WebSocket connection."""
        await websocket.accept()
        
        if admin_id not in self.active_connections:
            self.active_connections[admin_id] = set()
        
        self.active_connections[admin_id].add(websocket)
        logger.info(f"WebSocket connected for admin {admin_id}")
    
    def disconnect(self, websocket: WebSocket, admin_id: int):
        """Remove a WebSocket connection."""
        if admin_id in self.active_connections:
            self.active_connections[admin_id].discard(websocket)
            
            # Clean up empty sets
            if not self.active_connections[admin_id]:
                del self.active_connections[admin_id]
        
        logger.info(f"WebSocket disconnected for admin {admin_id}")
    
    async def send_personal_message(self, message: dict, admin_id: int):
        """Send a message to a specific admin's connections."""
        if admin_id in self.active_connections:
            # Send to all connections for this admin
            disconnected = set()
            
            for connection in self.active_connections[admin_id]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Failed to send message: {str(e)}")
                    disconnected.add(connection)
            
            # Clean up disconnected connections
            for conn in disconnected:
                self.active_connections[admin_id].discard(conn)
    
    async def broadcast(self, message: dict):
        """Broadcast a message to all connected admins."""
        disconnected = []
        
        for admin_id, connections in self.active_connections.items():
            for connection in connections:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Failed to broadcast to admin {admin_id}: {str(e)}")
                    disconnected.append((admin_id, connection))
        
        # Clean up disconnected connections
        for admin_id, conn in disconnected:
            if admin_id in self.active_connections:
                self.active_connections[admin_id].discard(conn)
    
    async def send_notification(
        self,
        admin_id: int,
        title: str,
        message: str,
        notification_type: str = "info",
        link: str = None
    ):
        """Send a notification to a specific admin."""
        notification = {
            "type": "notification",
            "data": {
                "title": title,
                "message": message,
                "notification_type": notification_type,
                "link": link,
                "timestamp": datetime.now().isoformat()
            }
        }
        
        await self.send_personal_message(notification, admin_id)
    
    async def send_download_notification(
        self,
        admin_id: int,
        video_title: str,
        status: str = "success"
    ):
        """Send a download notification."""
        await self.send_notification(
            admin_id=admin_id,
            title="New Download",
            message=f"Video downloaded: {video_title}",
            notification_type=status,
            link="/admin/dashboard?section=analytics"
        )
    
    async def send_stats_update(self, admin_id: int, stats: dict):
        """Send real-time stats update."""
        message = {
            "type": "stats_update",
            "data": stats,
            "timestamp": datetime.now().isoformat()
        }
        
        await self.send_personal_message(message, admin_id)
    
    async def broadcast_stats_update(self, stats: dict):
        """Broadcast stats update to all admins."""
        message = {
            "type": "stats_update",
            "data": stats,
            "timestamp": datetime.now().isoformat()
        }
        
        await self.broadcast(message)
    
    def get_connection_count(self, admin_id: int = None) -> int:
        """Get number of active connections."""
        if admin_id:
            return len(self.active_connections.get(admin_id, set()))
        else:
            return sum(len(conns) for conns in self.active_connections.values())


# Global connection manager instance
manager = ConnectionManager()

