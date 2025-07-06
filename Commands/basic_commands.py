import discord
from discord import Embed, app_commands
from discord.ext import commands


class BasicCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        
    @discord.app_commands.allowed_installs(guilds=True, users=True)
    @discord.app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @app_commands.command(name="help", description="List all available commands.")
    async def help(self, interaction: discord.Interaction):
        embed = Embed(
            title="📖 ZobbifAI Commands",
            description="**Last updated July 2025**"
        )

        def format_command_path(command: app_commands.Command, prefix="") -> list[str]:
            lines = []
            path = f"{prefix}{command.name}"
            if isinstance(command, app_commands.Group):
                for sub in command.commands:
                    lines.extend(format_command_path(sub, f"{path} "))
            else:
                desc = command.description or "No description"
                lines.append(f"/{path} — {desc}")
            return lines

        # Collect all formatted command lines
        command_lines = []
        for cmd in self.bot.tree.get_commands():
            command_lines.extend(format_command_path(cmd))

        # Optional: Group lines into sections if you want
        for line in command_lines:
            embed.add_field(name=line.split(" — ")[0], value=line.split(" — ")[1], inline=False)

        await interaction.response.send_message(embed=embed)

    # @app_commands.command(name="ping", description="Check if the bot is alive.")
    # async def ping(self, interaction: discord.Interaction):
    #     await interaction.response.send_message("🏓 Pong!")

    @discord.app_commands.allowed_installs(guilds=True, users=True)
    @discord.app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @app_commands.command(name="about", description="Info about the bot.")
    async def about(self, interaction: discord.Interaction):
        await interaction.response.send_message("I'm a bot created by ZobbifAI. I can help you with various tasks and provide information. Use `/help` to see what I can do!")


async def setup(bot: commands.Bot):
    await bot.add_cog(BasicCommands(bot))
