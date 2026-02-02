"""
Player Tracking Cog
"""

import discord
from discord.ext import commands
from discord import app_commands
import logging

logger = logging.getLogger('RustPlusBot.Tracking')

class Tracking(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="track", description="Track en spiller")
    @app_commands.describe(player_name="Spillernavn")
    async def track(self, interaction: discord.Interaction, player_name: str):
        await interaction.response.defer()
        await interaction.followup.send(f"🔍 Tracker nu **{player_name}** (feature under udvikling)")

async def setup(bot):
    await bot.add_cog(Tracking(bot))
