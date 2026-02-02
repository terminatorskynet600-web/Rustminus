"""
FCM Listener - Manual Pairing
"""

from rustplus import FCMListener
import json
import logging
from pathlib import Path
from datetime import datetime
import asyncio

logger = logging.getLogger('RustPlusBot.FCM')

class AutoPairing(FCMListener):
    def __init__(self, fcm_details, devices_file, bot=None):
        super().__init__(fcm_details)
        self.devices_file = Path(devices_file)
        self.bot = bot
        self.devices = self.load_devices()
        self.pending_pairs = {}
    
    def load_devices(self):
        if self.devices_file.exists():
            with open(self.devices_file, 'r') as f:
                return json.load(f)
        return {}
    
    def save_devices(self):
        self.devices_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.devices_file, 'w') as f:
            json.dump(self.devices, f, indent=2)
    
    def on_notification(self, obj, notification, data_message):
        try:
            if notification and isinstance(notification, dict):
                if 'body' in notification:
                    try:
                        body_data = json.loads(notification['body'])
                        
                        if all(k in body_data for k in ['ip', 'port', 'playerId', 'playerToken']):
                            from utils.rust_api import rust
                            rust.update_from_fcm(body_data)
                        
                        if 'entityId' in body_data and body_data.get('type') == 'entity':
                            self.handle_device_pairing_request(body_data)
                        
                    except json.JSONDecodeError:
                        pass
        except Exception as e:
            logger.error(f"Error: {e}")
    
    def handle_device_pairing_request(self, data):
        try:
            entity_id = int(data.get('entityId'))
            entity_name = data.get('entityName', f'Device_{entity_id}')
            entity_type = data.get('entityType', '1')
            
            type_map = {'1': 'switch', '2': 'alarm', '3': 'storage_monitor'}
            device_type = type_map.get(str(entity_type), 'unknown')
            
            self.pending_pairs[entity_id] = {
                'entity_id': entity_id,
                'name': entity_name,
                'type': device_type,
                'entity_type_code': entity_type,
                'timestamp': datetime.now().isoformat()
            }
            
            logger.info(f"📱 Pairing: {entity_name} ({entity_id})")
            
            if self.bot:
                asyncio.run_coroutine_threadsafe(
                    self.send_pairing_notification(entity_id, entity_name, device_type),
                    self.bot.loop
                )
            
        except Exception as e:
            logger.error(f"Pairing error: {e}")
    
    async def send_pairing_notification(self, entity_id, entity_name, device_type):
        try:
            import discord
            
            for guild in self.bot.guilds:
                # Get configured pairing channel
                channel_id = self.bot.get_pairing_channel(guild.id)
                
                if channel_id:
                    channel = guild.get_channel(channel_id)
                    if channel:
                        embed = discord.Embed(
                            title="📱 Device Pairing Request",
                            color=discord.Color.blue()
                        )
                        
                        embed.add_field(name="Device", value=entity_name, inline=False)
                        embed.add_field(name="ID", value=f"`{entity_id}`", inline=True)
                        embed.add_field(name="Type", value=device_type, inline=True)
                        
                        embed.set_footer(text=f"Use: /rplpair {entity_id} <name>")
                        
                        await channel.send(embed=embed)
                        logger.info(f"✅ Sent to {guild.name}")
                        return
                        
        except Exception as e:
            logger.error(f"Send error: {e}")
    
    def approve_pairing(self, entity_id, custom_name):
        if entity_id not in self.pending_pairs:
            return False, "Pairing not found"
        
        device_data = self.pending_pairs[entity_id]
        device_key = custom_name.lower().replace(' ', '_')
        
        self.devices[device_key] = {
            'entity_id': entity_id,
            'name': device_data['name'],
            'display_name': custom_name,
            'type': device_data['type'],
            'entity_type_code': device_data['entity_type_code'],
            'auto_added': False,
            'added_at': datetime.now().isoformat()
        }
        
        self.save_devices()
        del self.pending_pairs[entity_id]
        
        logger.info(f"✅ Paired: {custom_name}")
        return True, f"Paired as '{custom_name}'"