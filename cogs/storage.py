"""
Storage Monitor Cog
"""

import discord
from discord.ext import commands
from discord import app_commands
import logging
import json
from pathlib import Path
from utils.rust_api import rust

logger = logging.getLogger('RustPlusBot.Storage')

class Storage(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.storage_file = Path("data/storage.json")
        self.storage_monitors = self.load_monitors()
    
    def load_monitors(self):
        if self.storage_file.exists():
            with open(self.storage_file, 'r') as f:
                return json.load(f)
        return {}
    
    def save_monitors(self):
        self.storage_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.storage_file, 'w') as f:
            json.dump(self.storage_monitors, f, indent=2)
    
    @app_commands.command(name="storage", description="Vis storage monitor indhold")
    @app_commands.describe(name="Navn på storage monitor")
    async def storage(self, interaction: discord.Interaction, name: str):
        await interaction.response.defer()
        
        if name.lower() not in self.storage_monitors:
            await interaction.followup.send(f"❌ Storage monitor **{name}** ikke fundet")
            return
        
        entity_id = self.storage_monitors[name.lower()]['entity_id']
        contents = await rust.get_contents(entity_id)
        
        if not contents:
            await interaction.followup.send("❌ Kunne ikke hente indhold")
            return
        
        embed = discord.Embed(title=f"📦 {name}", color=discord.Color.gold())
        
        if hasattr(contents, 'items') and contents.items:
            for item in contents.items:
                embed.add_field(
                    name=item.name if hasattr(item, 'name') else "Item",
                    value=f"Amount: {item.quantity if hasattr(item, 'quantity') else 0}",
                    inline=True
                )
        else:
            embed.description = "Tom"
        
        await interaction.followup.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Storage(bot))
