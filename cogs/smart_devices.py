"""
Smart Devices Control Cog
"""

import discord
from discord.ext import commands
from discord import app_commands
import logging
import json
from pathlib import Path
from utils.rust_api import rust

logger = logging.getLogger('RustPlusBot.SmartDevices')

class SmartDevices(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.devices_file = Path('data/devices.json')
        self.devices = self.load_devices()
    
    def load_devices(self):
        """Load devices from JSON file"""
        try:
            if self.devices_file.exists():
                with open(self.devices_file, 'r') as f:
                    devices = json.load(f)
                    logger.info(f"✅ Loaded {len(devices)} devices from {self.devices_file}")
                    return devices
            else:
                logger.warning(f"⚠️ No devices file found at {self.devices_file}")
                return {}
        except Exception as e:
            logger.error(f"Error loading devices: {e}")
            return {}
    
    def save_devices(self):
        """Save devices to JSON file"""
        try:
            self.devices_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.devices_file, 'w') as f:
                json.dump(self.devices, f, indent=2)
            logger.info(f"💾 Saved {len(self.devices)} devices")
        except Exception as e:
            logger.error(f"Error saving devices: {e}")
    
    def reload_devices(self):
        """Reload devices from file"""
        self.devices = self.load_devices()
    
    @app_commands.command(name="devices", description="Vis alle gemte enheder")
    async def devices(self, interaction: discord.Interaction):
        """List all saved devices"""
        # Reload devices to get latest
        self.reload_devices()
        
        if not self.devices:
            await interaction.response.send_message("📭 Ingen gemte enheder. Pair en device in-game for at auto-tilføje den!")
            return
        
        embed = discord.Embed(
            title="🔌 Gemte Smart Devices",
            description=f"Total: {len(self.devices)} enheder",
            color=discord.Color.blue()
        )
        
        for key, device in self.devices.items():
            device_type = device.get('type', 'unknown')
            entity_id = device.get('entity_id', 'N/A')
            name = device.get('name', key)
            display_name = device.get('display_name', name)
            auto_added = "🤖 Auto" if device.get('auto_added') else "👤 Manual"
            
            value_parts = [
                f"**Display Name:** `{display_name}`",
                f"**Type:** `{device_type}`",
                f"**ID:** `{entity_id}`",
                f"**Key:** `{key}`",
                f"{auto_added}"
            ]
            
            embed.add_field(
                name=f"📍 {name}",
                value="\n".join(value_parts),
                inline=False
            )
        
        embed.set_footer(text="Brug /on, /off, /toggle eller !on, !off, !toggle i team chat")
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="on", description="Tænd en smart device")
    async def turn_on(self, interaction: discord.Interaction, device: str):
        """Turn on a device"""
        await interaction.response.defer()
        
        # Reload devices
        self.reload_devices()
        
        # Find device
        device_info = self.find_device(device)
        if not device_info:
            await interaction.followup.send(f"❌ Device `{device}` ikke fundet. Brug `/devices` for at se alle.")
            return
        
        entity_id = device_info['entity_id']
        display_name = device_info.get('display_name') or device_info.get('name', device)
        
        try:
            result = await rust.turn_on_smart_switch(entity_id)
            if result:
                await interaction.followup.send(f"✅ Tændte `{display_name}`")
            else:
                await interaction.followup.send(f"❌ Kunne ikke tænde `{display_name}`")
        except Exception as e:
            logger.error(f"Error turning on device: {e}")
            await interaction.followup.send(f"❌ Fejl: {e}")
    
    @app_commands.command(name="off", description="Sluk en smart device")
    async def turn_off(self, interaction: discord.Interaction, device: str):
        """Turn off a device"""
        await interaction.response.defer()
        
        # Reload devices
        self.reload_devices()
        
        # Find device
        device_info = self.find_device(device)
        if not device_info:
            await interaction.followup.send(f"❌ Device `{device}` ikke fundet. Brug `/devices` for at se alle.")
            return
        
        entity_id = device_info['entity_id']
        display_name = device_info.get('display_name') or device_info.get('name', device)
        
        try:
            result = await rust.turn_off_smart_switch(entity_id)
            if result:
                await interaction.followup.send(f"🔴 Slukkede `{display_name}`")
            else:
                await interaction.followup.send(f"❌ Kunne ikke slukke `{display_name}`")
        except Exception as e:
            logger.error(f"Error turning off device: {e}")
            await interaction.followup.send(f"❌ Fejl: {e}")
    
    @app_commands.command(name="toggle", description="Toggle en smart device")
    async def toggle(self, interaction: discord.Interaction, device: str):
        """Toggle a device"""
        await interaction.response.defer()
        
        # Reload devices
        self.reload_devices()
        
        # Find device
        device_info = self.find_device(device)
        if not device_info:
            await interaction.followup.send(f"❌ Device `{device}` ikke fundet. Brug `/devices` for at se alle.")
            return
        
        entity_id = device_info['entity_id']
        display_name = device_info.get('display_name') or device_info.get('name', device)
        
        try:
            # Get current state
            info = await rust.get_entity_info(entity_id)
            if not info:
                await interaction.followup.send(f"❌ Kunne ikke hente status for `{display_name}`")
                return
            
            # Toggle based on current state
            if info.value:
                result = await rust.turn_off_smart_switch(entity_id)
                status = "🔴 Slukket"
            else:
                result = await rust.turn_on_smart_switch(entity_id)
                status = "✅ Tændt"
            
            if result:
                await interaction.followup.send(f"{status} `{display_name}`")
            else:
                await interaction.followup.send(f"❌ Kunne ikke toggle `{display_name}`")
        except Exception as e:
            logger.error(f"Error toggling device: {e}")
            await interaction.followup.send(f"❌ Fejl: {e}")
    
    @app_commands.command(name="status", description="Vis status for en device")
    async def status(self, interaction: discord.Interaction, device: str):
        """Show device status"""
        await interaction.response.defer()
        
        # Reload devices
        self.reload_devices()
        
        # Find device
        device_info = self.find_device(device)
        if not device_info:
            await interaction.followup.send(f"❌ Device `{device}` ikke fundet.")
            return
        
        entity_id = device_info['entity_id']
        display_name = device_info.get('display_name') or device_info.get('name', device)
        
        try:
            info = await rust.get_entity_info(entity_id)
            if not info:
                await interaction.followup.send(f"❌ Kunne ikke hente status")
                return
            
            status_icon = "🟢" if info.value else "🔴"
            status_text = "ON" if info.value else "OFF"
            
            embed = discord.Embed(
                title=f"{status_icon} {display_name}",
                color=discord.Color.green() if info.value else discord.Color.red()
            )
            
            embed.add_field(name="Status", value=status_text, inline=True)
            embed.add_field(name="Type", value=device_info.get('type', 'unknown'), inline=True)
            embed.add_field(name="Entity ID", value=entity_id, inline=True)
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error getting status: {e}")
            await interaction.followup.send(f"❌ Fejl: {e}")
    
    @app_commands.command(name="add-device", description="Tilføj device manuelt")
    async def add_device(
        self,
        interaction: discord.Interaction,
        name: str,
        entity_id: int,
        device_type: str = "switch"
    ):
        """Manually add a device"""
        device_key = name.lower().replace(' ', '_')
        
        self.devices[device_key] = {
            'entity_id': entity_id,
            'name': name,
            'display_name': name,
            'type': device_type,
            'auto_added': False
        }
        
        self.save_devices()
        
        await interaction.response.send_message(
            f"✅ Tilføjet device: `{name}` (ID: {entity_id})\n"
            f"Brug `/on {device_key}` eller `!on {name}` i team chat"
        )
    
    @app_commands.command(name="rename-device", description="Omdøb en device")
    async def rename_device(
        self,
        interaction: discord.Interaction,
        device: str,
        new_name: str
    ):
        """Rename a device"""
        self.reload_devices()
        
        # Find device
        device_key = None
        for key in self.devices.keys():
            if key == device.lower().replace(' ', '_'):
                device_key = key
                break
        
        if not device_key:
            await interaction.response.send_message(f"❌ Device `{device}` ikke fundet")
            return
        
        # Update display name
        old_name = self.devices[device_key].get('display_name') or self.devices[device_key].get('name', device)
        self.devices[device_key]['display_name'] = new_name
        self.save_devices()
        
        await interaction.response.send_message(
            f"✅ Device omdøbt:\n"
            f"**Før:** `{old_name}`\n"
            f"**Nu:** `{new_name}`\n\n"
            f"Brug `!on {new_name}` i team chat eller `/on {device_key}` i Discord"
        )
    
    @app_commands.command(name="remove-device", description="Fjern en device")
    async def remove_device(self, interaction: discord.Interaction, device: str):
        """Remove a device"""
        self.reload_devices()
        
        device_key = device.lower().replace(' ', '_')
        
        if device_key not in self.devices:
            await interaction.response.send_message(f"❌ Device `{device}` ikke fundet")
            return
        
        device_name = self.devices[device_key].get('display_name') or self.devices[device_key].get('name', device)
        del self.devices[device_key]
        self.save_devices()
        
        await interaction.response.send_message(f"🗑️ Fjernede device: `{device_name}`")
    
    def find_device(self, device_input):
        """
        Find device by key, name, or display_name
        Returns device dict or None
        """
        device_key = device_input.lower().replace(' ', '_')
        
        # Try exact key match first
        if device_key in self.devices:
            return self.devices[device_key]
        
        # Try to find by display_name or name
        for key, device in self.devices.items():
            if device.get('display_name', '').lower() == device_input.lower():
                return device
            if device.get('name', '').lower() == device_input.lower():
                return device
        
        return None

async def setup(bot):
    await bot.add_cog(SmartDevices(bot))