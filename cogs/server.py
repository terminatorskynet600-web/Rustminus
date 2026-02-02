"""
Server Information Cog
"""

import discord
from discord.ext import commands, tasks
from discord import app_commands
import logging
from utils.rust_api import rust

logger = logging.getLogger('RustPlusBot.Server')

class Server(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.auto_update.start()
    
    @app_commands.command(name="server", description="Vis server information")
    async def server(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        info = await rust.get_info()
        if not info:
            await interaction.followup.send("❌ Kunne ikke hente server info")
            return
        
        time_data = await rust.get_time()
        time_str = self.format_time(time_data) if time_data else "Ukendt"
        
        embed = discord.Embed(
            title=f"🎮 {info.name}",
            color=discord.Color.blue()
        )
        
        embed.add_field(name="👥 Spillere", value=f"{info.players}/{info.max_players}", inline=True)
        embed.add_field(name="⏳ Queue", value=f"{info.queued_players}", inline=True)
        embed.add_field(name="🕐 Server Tid", value=time_str, inline=True)
        
        embed.set_footer(text="Rust+ Bot")
        embed.timestamp = discord.utils.utcnow()
        
        await interaction.followup.send(embed=embed)
    
    @app_commands.command(name="pop", description="Vis server population")
    async def pop(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        info = await rust.get_info()
        if not info:
            await interaction.followup.send("❌ Kunne ikke hente server info")
            return
        
        percent = (info.players / info.max_players * 100) if info.max_players > 0 else 0
        bar_length = 20
        filled = int(bar_length * percent / 100)
        bar = "█" * filled + "░" * (bar_length - filled)
        
        embed = discord.Embed(
            title="📊 Server Population",
            description=f"```{bar}```\n{info.players}/{info.max_players} spillere ({percent:.1f}%)",
            color=discord.Color.blue()
        )
        
        if info.queued_players > 0:
            embed.add_field(name="⏳ I kø", value=f"{info.queued_players} spillere")
        
        await interaction.followup.send(embed=embed)
    
    @app_commands.command(name="time", description="Vis in-game tid")
    async def time(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        time_data = await rust.get_time()
        if not time_data:
            await interaction.followup.send("❌ Kunne ikke hente tiden")
            return
        
        time_str = self.format_time(time_data)
        
        embed = discord.Embed(
            title="🕐 Server Tid",
            description=time_str,
            color=discord.Color.blue()
        )
        
        await interaction.followup.send(embed=embed)
    
    def format_time(self, time_data):
        if not time_data:
            return "Ukendt"
        if isinstance(time_data, str):
            return time_data
        try:
            if hasattr(time_data, 'time'):
                time_value = float(time_data.time)
            else:
                time_value = float(time_data)
            hours = int(time_value)
            minutes = int((time_value - hours) * 60)
            icon = "☀️" if 6 <= hours < 18 else "🌙"
            return f"{icon} {hours:02d}:{minutes:02d}"
        except:
            return "12:00"
    
    @tasks.loop(minutes=10)
    async def auto_update(self):
        pass
    
    @auto_update.before_loop
    async def before_update(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(Server(bot))
