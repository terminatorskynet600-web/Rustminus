"""
Server Events Cog
"""

import discord
from discord.ext import commands
from discord import app_commands
import logging
from utils.rust_api import rust

logger = logging.getLogger('RustPlusBot.Events')

class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="events", description="Vis server events")
    async def events(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        markers = await rust.get_markers()
        if not markers:
            await interaction.followup.send("❌ Kunne ikke hente events")
            return
        
        embed = discord.Embed(title="📍 Server Events", color=discord.Color.blue())
        
        event_types = {
            2: "🚁 Patrol Helicopter",
            4: "🚢 Cargo Ship",
            5: "💥 CH47 Chinook",
            8: "🏖️ Locked Crate"
        }
        
        events_found = False
        if hasattr(markers, 'markers'):
            for marker in markers.markers:
                if marker.type in event_types:
                    events_found = True
                    embed.add_field(
                        name=event_types[marker.type],
                        value=f"X: {marker.x:.0f}, Y: {marker.y:.0f}",
                        inline=True
                    )
        
        if not events_found:
            embed.description = "Ingen aktive events lige nu"
        
        await interaction.followup.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Events(bot))
