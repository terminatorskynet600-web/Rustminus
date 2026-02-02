"""
Team Tracker Cog - Auto-updating team member status display
"""

import discord
from discord.ext import commands, tasks
from discord import app_commands
import logging
import json
from pathlib import Path
from datetime import datetime, timedelta
from utils.rust_api import rust

logger = logging.getLogger('RustPlusBot.TeamTracker')

class TeamTracker(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.tracker_file = Path('data/team_trackers.json')
        self.trackers = self.load_trackers()
        self.member_data = {}  # Store member info with timestamps
        self.update_trackers.start()
    
    def load_trackers(self):
        """Load saved team tracker configurations"""
        if self.tracker_file.exists():
            with open(self.tracker_file, 'r') as f:
                return json.load(f)
        return {}
    
    def save_trackers(self):
        """Save team tracker configurations"""
        self.tracker_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.tracker_file, 'w') as f:
            json.dump(self.trackers, f, indent=2)
    
    @app_commands.command(name="team-tracker-setup", description="Setup auto-updating team tracker")
    @app_commands.describe(
        server_name="Server name to display (e.g., EU TideRust Solo/Duo/Trio/QuadNoob)",
        friendly="Is this a friendly server?",
        wipe_schedule="Wipe schedule (e.g., Monthly/No BP Wipes)"
    )
    async def setup_tracker(
        self,
        interaction: discord.Interaction,
        server_name: str = "EU TideRust Solo/Duo/Trio/QuadNoob",
        friendly: bool = True,
        wipe_schedule: str = "Friendly/Monthly/No BP Wipes"
    ):
        """Setup team tracker in current channel"""
        await interaction.response.defer()
        
        # Get initial team data
        team_info = await rust.get_team_info()
        if not team_info or not hasattr(team_info, 'members') or not team_info.members:
            await interaction.followup.send("❌ Could not get team info. Make sure you're connected to Rust+")
            return
        
        # Create initial embed
        embed = await self.create_team_embed(team_info, server_name, wipe_schedule)
        
        # Send the embed
        message = await interaction.channel.send(embed=embed)
        
        # Save tracker configuration
        tracker_key = f"{interaction.guild_id}_{interaction.channel_id}"
        self.trackers[tracker_key] = {
            'guild_id': interaction.guild_id,
            'channel_id': interaction.channel_id,
            'message_id': message.id,
            'server_name': server_name,
            'wipe_schedule': wipe_schedule,
            'friendly': friendly,
            'leader_id': team_info.leader_steam_id if hasattr(team_info, 'leader_steam_id') else None
        }
        self.save_trackers()
        
        await interaction.followup.send(
            f"✅ Team tracker setup complete!\n"
            f"The tracker will auto-update every 30 seconds.",
            ephemeral=True
        )
    
    async def create_team_embed(self, team_info, server_name, wipe_schedule):
        """Create the team tracker embed"""
        member_count = len(team_info.members) if hasattr(team_info, 'members') else 0
        
        embed = discord.Embed(
            title=f"Team Members ({member_count})",
            color=0x2b2d31,  # Dark gray color matching the image
            timestamp=datetime.utcnow()
        )
        
        # Get leader info
        leader_name = "Unknown"
        leader_id = None
        if hasattr(team_info, 'leader_steam_id'):
            leader_id = team_info.leader_steam_id
            for member in team_info.members:
                if member.steam_id == leader_id:
                    leader_name = member.name
                    break
        
        # Add team leader field
        if leader_id:
            for member in team_info.members:
                if member.steam_id == leader_id:
                    status_text = self.get_member_status_text(member)
                    embed.add_field(
                        name=f"Team Leader: {member.name}",
                        value=status_text,
                        inline=False
                    )
                    # Store member data
                    self.update_member_data(member)
                    break
        
        # Add other team members
        for member in team_info.members:
            if hasattr(team_info, 'leader_steam_id') and member.steam_id == team_info.leader_steam_id:
                continue  # Skip leader as we already added them
            
            status_text = self.get_member_status_text(member)
            embed.add_field(
                name=member.name,
                value=status_text,
                inline=False
            )
            # Store member data
            self.update_member_data(member)
        
        # Add server info footer
        wipe_date = datetime.utcnow().strftime("%d/%m/%Y %H:%M")
        footer_text = f"[{server_name} {wipe_schedule}] • {wipe_date}"
        embed.set_footer(text=footer_text)
        
        return embed
    
    def get_member_status_text(self, member):
        """Generate status text for a member"""
        # Get grid coordinates
        grid_x = self.get_grid_letter(member.x)
        grid_y = self.get_grid_number(member.y)
        location = f"{grid_x}{grid_y}"
        
        # Calculate last seen time
        member_key = str(member.steam_id)
        if member_key in self.member_data:
            last_online = self.member_data[member_key].get('last_online')
            if last_online and not member.is_online:
                time_diff = datetime.utcnow() - datetime.fromisoformat(last_online)
                last_seen_text = self.format_time_ago(time_diff)
            else:
                last_seen_text = "just now"
        else:
            last_seen_text = "just now"
        
        # Format status
        if member.is_online:
            status_icon = "🟢"
            status_text = "ONLINE"
        else:
            status_icon = "🔴"
            status_text = "OFFLINE"
        
        return f"{status_icon} {status_text}; located @ {location}; last seen {last_seen_text}"
    
    def update_member_data(self, member):
        """Update stored member data for tracking last seen"""
        member_key = str(member.steam_id)
        now = datetime.utcnow().isoformat()
        
        if member_key not in self.member_data:
            self.member_data[member_key] = {
                'name': member.name,
                'last_online': now if member.is_online else None,
                'last_seen': now,
                'was_online': member.is_online
            }
        else:
            # Update last online time if currently online
            if member.is_online:
                self.member_data[member_key]['last_online'] = now
                self.member_data[member_key]['was_online'] = True
            elif self.member_data[member_key]['was_online']:
                # Just went offline, record the time
                self.member_data[member_key]['was_online'] = False
            
            self.member_data[member_key]['last_seen'] = now
            self.member_data[member_key]['name'] = member.name
    
    def get_grid_letter(self, x):
        """Convert X coordinate to grid letter"""
        # Rust map is typically 0-4000 or similar, divided into grid squares
        # Adjust based on your server's map size
        grid_size = 146.3  # Approximate size per grid square
        letter_index = int(x / grid_size)
        letters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        if 0 <= letter_index < len(letters):
            return letters[letter_index]
        return 'A'
    
    def get_grid_number(self, y):
        """Convert Y coordinate to grid number"""
        grid_size = 146.3  # Approximate size per grid square
        number = int(y / grid_size)
        return str(number)
    
    def format_time_ago(self, time_diff):
        """Format timedelta to human readable 'time ago' string"""
        seconds = int(time_diff.total_seconds())
        
        if seconds < 60:
            return "just now"
        elif seconds < 3600:
            minutes = seconds // 60
            return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
        elif seconds < 86400:
            hours = seconds // 3600
            return f"{hours} hour{'s' if hours != 1 else ''} ago"
        else:
            days = seconds // 86400
            return f"{days} day{'s' if days != 1 else ''} ago"
    
    @tasks.loop(seconds=30)
    async def update_trackers(self):
        """Auto-update all team trackers"""
        if not rust._ready:
            return
        
        try:
            # Get current team info
            team_info = await rust.get_team_info()
            if not team_info or not hasattr(team_info, 'members'):
                return
            
            # Update each tracker
            for tracker_key, tracker_data in list(self.trackers.items()):
                try:
                    guild = self.bot.get_guild(tracker_data['guild_id'])
                    if not guild:
                        continue
                    
                    channel = guild.get_channel(tracker_data['channel_id'])
                    if not channel:
                        continue
                    
                    try:
                        message = await channel.fetch_message(tracker_data['message_id'])
                    except discord.NotFound:
                        logger.warning(f"Tracker message not found: {tracker_key}")
                        continue
                    
                    # Create updated embed
                    embed = await self.create_team_embed(
                        team_info,
                        tracker_data['server_name'],
                        tracker_data['wipe_schedule']
                    )
                    
                    # Update the message
                    await message.edit(embed=embed)
                    
                except Exception as e:
                    logger.error(f"Error updating tracker {tracker_key}: {e}")
                    
        except Exception as e:
            logger.error(f"Error in update_trackers loop: {e}")
    
    @update_trackers.before_loop
    async def before_update(self):
        """Wait for bot to be ready before starting updates"""
        await self.bot.wait_until_ready()
        # Wait for Rust+ connection
        import asyncio
        for i in range(60):
            if rust._ready:
                logger.info("✅ Team tracker auto-update started!")
                return
            await asyncio.sleep(1)
    
    @app_commands.command(name="team-tracker-remove", description="Remove team tracker from this channel")
    async def remove_tracker(self, interaction: discord.Interaction):
        """Remove team tracker from current channel"""
        tracker_key = f"{interaction.guild_id}_{interaction.channel_id}"
        
        if tracker_key in self.trackers:
            del self.trackers[tracker_key]
            self.save_trackers()
            await interaction.response.send_message("✅ Team tracker removed from this channel", ephemeral=True)
        else:
            await interaction.response.send_message("❌ No team tracker found in this channel", ephemeral=True)
    
    @app_commands.command(name="team-tracker-list", description="List all active team trackers")
    async def list_trackers(self, interaction: discord.Interaction):
        """List all active team trackers in this server"""
        guild_trackers = {k: v for k, v in self.trackers.items() if v['guild_id'] == interaction.guild_id}
        
        if not guild_trackers:
            await interaction.response.send_message("📭 No team trackers in this server", ephemeral=True)
            return
        
        embed = discord.Embed(
            title="📊 Active Team Trackers",
            color=discord.Color.blue()
        )
        
        for tracker_key, tracker_data in guild_trackers.items():
            channel = self.bot.get_channel(tracker_data['channel_id'])
            channel_mention = channel.mention if channel else f"Unknown ({tracker_data['channel_id']})"
            
            embed.add_field(
                name=f"Tracker in {channel_mention}",
                value=f"Server: {tracker_data['server_name']}\nSchedule: {tracker_data['wipe_schedule']}",
                inline=False
            )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    def cog_unload(self):
        """Clean up when cog is unloaded"""
        self.update_trackers.cancel()

async def setup(bot):
    await bot.add_cog(TeamTracker(bot))