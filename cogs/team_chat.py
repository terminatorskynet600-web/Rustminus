"""
Team Chat Command Listener
"""

import discord
from discord.ext import commands, tasks
import logging
import json
from pathlib import Path
from utils.rust_api import rust
import asyncio

logger = logging.getLogger('RustPlusBot.TeamChat')

class TeamChat(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.devices_file = Path('data/devices.json')
        self.last_message_id = None
        self.monitor_chat.start()
    
    def load_devices(self):
        if self.devices_file.exists():
            with open(self.devices_file, 'r') as f:
                return json.load(f)
        return {}
    
    @tasks.loop(seconds=3)
    async def monitor_chat(self):
        if not rust._ready:
            return
            
        try:
            chat = await rust.get_team_chat()
            
            if hasattr(chat, 'error'):
                return
            
            if not chat or len(chat) == 0:
                return
            
            latest = chat[-1]
            
            if self.last_message_id == latest.time:
                return
            
            self.last_message_id = latest.time
            
            message = latest.message.strip()
            logger.info(f"📬 [{latest.name}]: {message}")
            
            if not message.startswith('!'):
                return
            
            parts = message.split(' ', 1)
            command = parts[0].lower()
            device_name = parts[1] if len(parts) > 1 else None
            
            if command in ['!on', '!off', '!toggle']:
                if not device_name:
                    await rust.send_team_message("❌ Usage: !on <device>")
                    return
                
                await self.handle_device_command(command[1:], device_name)
            
        except Exception as e:
            logger.error(f"Error: {e}")
    
    async def handle_device_command(self, action, device_input):
        devices = self.load_devices()
        
        device_key = device_input.lower().replace(' ', '_')
        device = None
        
        if device_key in devices:
            device = devices[device_key]
        else:
            for key, dev in devices.items():
                display = dev.get('display_name', '').lower()
                name = dev.get('name', '').lower()
                if display == device_input.lower() or name == device_input.lower():
                    device = dev
                    break
        
        if not device:
            await rust.send_team_message(f"❌ '{device_input}' not found")
            return
        
        entity_id = device['entity_id']
        device_name = device.get('display_name') or device.get('name', device_input)
        
        logger.info(f"🎯 Attempting {action} on {entity_id}")
        
        try:
            if action == 'on':
                logger.info(f"Calling turn_on_smart_switch({entity_id})")
                result = await rust.turn_on_smart_switch(entity_id)
                logger.info(f"Result: {result}")
                if result:
                    await rust.send_team_message(f"✅ {device_name}")
                else:
                    await rust.send_team_message(f"❌ Failed to turn on")
                    logger.error("turn_on returned False")
            
            elif action == 'off':
                logger.info(f"Calling turn_off_smart_switch({entity_id})")
                result = await rust.turn_off_smart_switch(entity_id)
                logger.info(f"Result: {result}")
                if result:
                    await rust.send_team_message(f"🔴 {device_name}")
                else:
                    await rust.send_team_message(f"❌ Failed to turn off")
                    logger.error("turn_off returned False")
            
            elif action == 'toggle':
                logger.info(f"Getting entity info for {entity_id}")
                info = await rust.get_entity_info(entity_id)
                logger.info(f"Entity info: {info}")
                
                if info and not hasattr(info, 'error'):
                    if info.value:
                        result = await rust.turn_off_smart_switch(entity_id)
                        if result:
                            await rust.send_team_message(f"🔴 {device_name}")
                    else:
                        result = await rust.turn_on_smart_switch(entity_id)
                        if result:
                            await rust.send_team_message(f"✅ {device_name}")
                else:
                    await rust.send_team_message(f"❌ Can't get status")
                    logger.error(f"Entity info failed: {info}")
        
        except Exception as e:
            logger.error(f"Control error: {e}")
            import traceback
            logger.error(traceback.format_exc())
            await rust.send_team_message(f"❌ Error")
    
    @monitor_chat.before_loop
    async def before_monitor(self):
        await self.bot.wait_until_ready()
        
        for i in range(60):
            if rust._ready:
                logger.info("✅ Monitoring active!")
                return
            await asyncio.sleep(1)
    
    def cog_unload(self):
        self.monitor_chat.cancel()

async def setup(bot):
    await bot.add_cog(TeamChat(bot))