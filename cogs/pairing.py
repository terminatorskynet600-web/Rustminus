"""
Manual Device Pairing Cog
"""

import discord
from discord.ext import commands
from discord import app_commands
import logging
from pathlib import Path

logger = logging.getLogger('RustPlusBot.Pairing')

class Pairing(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="rplpair", description="Pair en device med custom navn")
    @app_commands.describe(
        entity_id="Device ID fra pairing notifikationen",
        name="Custom navn til devicen"
    )
    async def pair_device(self, interaction: discord.Interaction, entity_id: int, name: str):
        """Pair a device with custom name"""
        await interaction.response.defer()
        
        try:
            # Get FCM listener from bot
            if not hasattr(self.bot, 'fcm_listener') or not self.bot.fcm_listener:
                await interaction.followup.send("❌ FCM listener ikke aktiv")
                return
            
            # Approve pairing
            success, message = self.bot.fcm_listener.approve_pairing(entity_id, name)
            
            if success:
                embed = discord.Embed(
                    title="✅ Device Paired!",
                    description=f"Device successfully paired",
                    color=discord.Color.green()
                )
                
                embed.add_field(name="Name", value=name, inline=True)
                embed.add_field(name="ID", value=entity_id, inline=True)
                
                embed.set_footer(text=f"Use !on {name} in team chat or /on in Discord")
                
                await interaction.followup.send(embed=embed)
            else:
                await interaction.followup.send(f"❌ {message}")
                
        except Exception as e:
            logger.error(f"Pairing error: {e}")
            await interaction.followup.send(f"❌ Error: {e}")
    
    @app_commands.command(name="pending", description="Vis pending pairing requests")
    async def pending_pairs(self, interaction: discord.Interaction):
        """Show pending pairing requests"""
        await interaction.response.defer()
        
        if not hasattr(self.bot, 'fcm_listener') or not self.bot.fcm_listener:
            await interaction.followup.send("❌ FCM listener ikke aktiv")
            return
        
        pending = self.bot.fcm_listener.pending_pairs
        
        if not pending:
            await interaction.followup.send("📭 Ingen pending pairing requests")
            return
        
        embed = discord.Embed(
            title="📱 Pending Pairing Requests",
            color=discord.Color.blue()
        )
        
        for entity_id, data in pending.items():
            embed.add_field(
                name=data['name'],
                value=f"ID: {entity_id}\nType: {data['type']}\nUse: `/rplpair {entity_id} <name>`",
                inline=False
            )
        
        await interaction.followup.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Pairing(bot))