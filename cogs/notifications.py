"""
Notifications Cog
"""

import discord
from discord.ext import commands
from discord import app_commands
import logging

logger = logging.getLogger('RustPlusBot.Notifications')

class Notifications(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="alerts", description="Konfigurer alerts")
    async def alerts(self, interaction: discord.Interaction):
        await interaction.response.defer()
        await interaction.followup.send("🔔 Alert system (feature under udvikling)")

async def setup(bot):
    await bot.add_cog(Notifications(bot))
