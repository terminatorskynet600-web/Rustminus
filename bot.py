#!/usr/bin/env python3
"""
RustMinus Discord Bot
"""

import discord
from discord.ext import commands
import asyncio
import os
import sys
import logging
import json
import threading
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

log_dir = Path("data/logs")
log_dir.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data/logs/bot.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('RustPlusBot')

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True
intents.presences = True

class RustPlusBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix=os.getenv('BOT_PREFIX', '!'),
            intents=intents,
            help_command=None
        )
        self.initial_extensions = [
            'cogs.server',
            'cogs.smart_devices',
            'cogs.events',
            'cogs.team',
            'cogs.team_chat',
            'cogs.tracking',
            'cogs.storage',
            'cogs.cameras',
            'cogs.notifications',
            'cogs.pairing'
        ]
        self.fcm_listener = None
        self.config_file = Path('data/bot_config.json')
        self.config = self.load_config()
        
    def load_config(self):
        if self.config_file.exists():
            with open(self.config_file, 'r') as f:
                return json.load(f)
        return {}
    
    def save_config(self):
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=2)
        
    async def setup_hook(self):
        for ext in self.initial_extensions:
            try:
                await self.load_extension(ext)
                logger.info(f'✅ {ext}')
            except Exception as e:
                logger.error(f'❌ {ext}: {e}')
        
        self.start_fcm_listener()
        asyncio.create_task(self.auto_connect_rust())
    
    async def auto_connect_rust(self):
        await self.wait_until_ready()
        
        from utils.rust_api import rust
        
        for i in range(60):
            if rust.server_ip and rust.server_port and rust.steam_id and rust.player_token:
                success = await rust.connect()
                if success:
                    logger.info("✅ Rust+ connected!")
                    return
            await asyncio.sleep(1)
    
    def start_fcm_listener(self):
        try:
            from utils.fcm_listener import AutoPairing
            
            config_file = Path('rustplus.py.config.json')
            if not config_file.exists():
                return
            
            with open(config_file, 'r') as f:
                fcm_creds = json.load(f)
            
            if 'fcm_credentials' not in fcm_creds:
                return
            
            devices_file = Path('data/devices.json')
            self.fcm_listener = AutoPairing(fcm_creds, devices_file, self)
            
            listener_thread = threading.Thread(
                target=self.fcm_listener.start, 
                daemon=True,
                name='FCM-Listener'
            )
            listener_thread.start()
            
            logger.info('✅ FCM Listener (Manual Pairing)')
            
        except Exception as e:
            logger.error(f'FCM error: {e}')
    
    async def setup_guild_channels(self, guild):
        """Setup RustMinus channels on first join"""
        guild_id = str(guild.id)
        
        # Skip if already setup
        if guild_id in self.config.get('guilds', {}):
            return
        
        try:
            # Create category
            category = await guild.create_category("🎮 RustMinus")
            
            # Create pairing channel
            pairing_channel = await guild.create_text_channel(
                "device-pairing",
                category=category,
                topic="Device pairing notifications appear here"
            )
            
            # Create status channel
            status_channel = await guild.create_text_channel(
                "rust-status", 
                category=category,
                topic="Server status and info"
            )
            
            # Save config
            if 'guilds' not in self.config:
                self.config['guilds'] = {}
            
            self.config['guilds'][guild_id] = {
                'pairing_channel': pairing_channel.id,
                'status_channel': status_channel.id,
                'category': category.id
            }
            self.save_config()
            
            logger.info(f"✅ Created channels for {guild.name}")
            
            # Send welcome message
            embed = discord.Embed(
                title="🎮 RustMinus Bot Setup Complete!",
                description="Channels created successfully",
                color=discord.Color.green()
            )
            embed.add_field(
                name="📱 Device Pairing",
                value=f"Pairing notifications → {pairing_channel.mention}",
                inline=False
            )
            embed.add_field(
                name="💡 How to Use",
                value="1. Pair device in-game\n2. Use `/rplpair <id> <name>` here\n3. Control with `!on <name>` in team chat",
                inline=False
            )
            
            await pairing_channel.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error setting up channels: {e}")
    
    async def on_ready(self):
        logger.info(f'✅ {self.user.name}')
        logger.info(f'📊 {len(self.guilds)} guild(s)')
        
        # Setup channels for all guilds
        for guild in self.guilds:
            await self.setup_guild_channels(guild)
        
        # Sync commands
        try:
            synced = await self.tree.sync()
            logger.info(f'✅ Synced {len(synced)} commands')
        except Exception as e:
            logger.error(f'Sync error: {e}')
    
    async def on_guild_join(self, guild):
        """Setup channels when bot joins new server"""
        logger.info(f"Joined guild: {guild.name}")
        await self.setup_guild_channels(guild)
    
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandNotFound):
            return
        logger.error(f'Error: {error}')
    
    def get_pairing_channel(self, guild_id):
        """Get pairing channel for a guild"""
        guild_config = self.config.get('guilds', {}).get(str(guild_id))
        if guild_config:
            return guild_config.get('pairing_channel')
        return None
    
    async def close(self):
        logger.info('🛑 Shutting down...')
        await super().close()

def main():
    token = os.getenv('DISCORD_TOKEN')
    
    if not token:
        logger.error("❌ DISCORD_TOKEN not found!")
        sys.exit(1)
    
    bot = RustPlusBot()
    
    try:
        logger.info('🚀 Starting RustMinus...')
        bot.run(token, log_handler=None)
    except KeyboardInterrupt:
        logger.info("🛑 Stopped")
    except Exception as e:
        logger.error(f"❌ Crash: {e}")

if __name__ == "__main__":
    main()