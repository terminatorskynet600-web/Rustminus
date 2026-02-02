"""
Team Management Cog
"""

import discord
from discord.ext import commands
from discord import app_commands
import logging
from utils.rust_api import rust

logger = logging.getLogger('RustPlusBot.Team')

class Team(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="team", description="Vis team medlemmer")
    async def team(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        team = await rust.get_team_info()
        if not team or not hasattr(team, 'members') or not team.members:
            await interaction.followup.send("❌ Ingen team medlemmer fundet")
            return
        
        embed = discord.Embed(title="👥 Team Medlemmer", color=discord.Color.blue())
        
        for member in team.members:
            status = "🟢 Online" if member.is_online else "🔴 Offline"
            embed.add_field(
                name=member.name,
                value=f"{status}\nX: {member.x:.0f}, Y: {member.y:.0f}",
                inline=True
            )
        
        await interaction.followup.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Team(bot))
