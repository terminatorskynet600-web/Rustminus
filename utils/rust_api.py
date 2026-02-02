"""
Rust+ API Wrapper
"""

import os
from rustplus import RustSocket, ServerDetails
import logging

logger = logging.getLogger('RustPlusBot.RustAPI')

class RustConnection:
    def __init__(self):
        self.socket = None
        self.server_ip = os.getenv('RUST_SERVER_IP')
        self.server_port = os.getenv('RUST_SERVER_PORT') 
        self.steam_id = os.getenv('RUST_STEAM_ID')
        self.player_token = os.getenv('RUST_PLAYER_TOKEN')
        self._ready = False
        
    def update_from_fcm(self, fcm_body_data):
        self.server_ip = fcm_body_data.get('ip')
        self.server_port = fcm_body_data.get('port')
        self.steam_id = fcm_body_data.get('playerId')
        self.player_token = fcm_body_data.get('playerToken')
        logger.info(f"📡 FCM: {self.server_ip}:{self.server_port}")
        
    async def connect(self):
        if self._ready:
            return True
            
        if not all([self.server_ip, self.server_port, self.steam_id, self.player_token]):
            return False
        
        try:
            server_details = ServerDetails(
                str(self.server_ip),
                str(self.server_port),
                int(self.steam_id),
                int(self.player_token)
            )
            
            self.socket = RustSocket(server_details)
            await self.socket.connect()
            self._ready = True
            logger.info(f"✅ Connected!")
            return True
            
        except Exception as e:
            logger.error(f"Connect: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
    
    async def disconnect(self):
        if self.socket:
            try:
                await self.socket.disconnect()
                self._ready = False
            except:
                pass
    
    async def ensure_connected(self):
        if not self._ready:
            logger.warning("⚠️ Not ready, attempting reconnect...")
            await self.connect()
    
    async def get_info(self):
        await self.ensure_connected()
        if not self.socket:
            logger.error("❌ No socket in get_info")
            return None
        try:
            return await self.socket.get_info()
        except Exception as e:
            logger.error(f"get_info: {e}")
            return None
    
    async def get_time(self):
        await self.ensure_connected()
        if not self.socket:
            return None
        try:
            return await self.socket.get_time()
        except:
            return None
    
    async def get_team_chat(self):
        if not self._ready or not self.socket:
            return None
        try:
            return await self.socket.get_team_chat()
        except:
            return None
    
    async def send_team_message(self, message):
        await self.ensure_connected()
        if not self.socket:
            logger.error("❌ No socket for send_team_message")
            return False
        try:
            await self.socket.send_team_message(message)
            logger.info(f"✉️ {message}")
            return True
        except Exception as e:
            logger.error(f"send_team_message error: {e}")
            return False
    
    async def get_entity_info(self, entity_id):
        await self.ensure_connected()
        if not self.socket:
            logger.error(f"❌ No socket for get_entity_info({entity_id})")
            return None
        try:
            result = await self.socket.get_entity_info(entity_id)
            logger.info(f"📊 Entity {entity_id} info: {result}")
            return result
        except Exception as e:
            logger.error(f"get_entity_info error: {e}")
            return None
    
    async def turn_on_smart_switch(self, entity_id):
        logger.info(f"🔵 turn_on_smart_switch called for {entity_id}")
        logger.info(f"   _ready: {self._ready}, socket: {self.socket is not None}")
        
        await self.ensure_connected()
        
        if not self.socket:
            logger.error(f"❌ No socket for turn_on({entity_id})")
            return False
        
        try:
            logger.info(f"   Calling socket.set_entity_value({entity_id}, True)")
            await self.socket.set_entity_value(entity_id, True)
            logger.info(f"✅ ON: {entity_id}")
            return True
        except Exception as e:
            logger.error(f"turn_on error: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
    
    async def turn_off_smart_switch(self, entity_id):
        logger.info(f"🔴 turn_off_smart_switch called for {entity_id}")
        
        await self.ensure_connected()
        
        if not self.socket:
            logger.error(f"❌ No socket for turn_off({entity_id})")
            return False
        
        try:
            await self.socket.set_entity_value(entity_id, False)
            logger.info(f"🔴 OFF: {entity_id}")
            return True
        except Exception as e:
            logger.error(f"turn_off error: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
    
    async def get_markers(self):
        await self.ensure_connected()
        if not self.socket:
            return None
        try:
            return await self.socket.get_markers()
        except:
            return None
    
    async def get_team_info(self):
        await self.ensure_connected()
        if not self.socket:
            return None
        try:
            return await self.socket.get_team_info()
        except:
            return None
    
    async def get_map(self):
        await self.ensure_connected()
        if not self.socket:
            return None
        try:
            return await self.socket.get_map()
        except:
            return None
    
    async def get_contents(self, entity_id):
        await self.ensure_connected()
        if not self.socket:
            return None
        try:
            return await self.socket.get_entity_info(entity_id)
        except:
            return None

rust = RustConnection()