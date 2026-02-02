"""
Camera Surveillance Cog
"""

import discord
from discord.ext import commands
from discord import app_commands
import logging

logger = logging.getLogger('RustPlusBot.Cameras')

class Cameras(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="camera", description="Se kamera feed")
    @app_commands.describe(identifier="Kamera identifier")
    async def camera(self, interaction: discord.Interaction, identifier: str):
        await interaction.response.defer()
        await interaction.followup.send(f"📹 Henter kamera **{identifier}** (feature under udvikling)")

async def setup(bot):
    await bot.add_cog(Cameras(bot))
