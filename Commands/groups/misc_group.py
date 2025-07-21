import random
import discord, SQL.helper
import discord.ext.commands as commands
from discord import app_commands


fired_from_job = False

@discord.app_commands.allowed_installs(guilds=True, users=True)
@discord.app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
class MiscGroup(app_commands.Group):
    def __init__(self, cog: commands.Cog):
        super().__init__(name="misc", description="Miscellaneous commands group")
        self.cog = cog
        self._db = SQL.helper.Helper()

    async def set_contexts(self, bot: commands.Bot):
        for command in self.walk_commands():
            command.allowed_contexts = app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)

    @app_commands.command(name="roll", description="Roll a random number (1–100)")
    async def roll(self, interaction: discord.Interaction):
        number = random.randint(1, 100)
        await interaction.response.send_message(f"🎲 You rolled a **{number}**!")

    @app_commands.command(name="coinflip", description="Flip a coin")
    async def coinflip(self, interaction: discord.Interaction):
        result = random.choice(["Heads", "Tails"])
        await interaction.response.send_message(f"🪙 It's **{result}**!")

    @app_commands.command(name="8ball", description="Ask the magic 8-ball a question")
    async def eight_ball(self, interaction: discord.Interaction, question: str):
        responses = [
            "Yes.", "No.", "Maybe.", "Absolutely!", "Definitely not.",
            "Ask again later.", "Without a doubt.", "Very doubtful."
        ]
        answer = random.choice(responses)
        await interaction.response.send_message(f"🎱 **Question:** {question}\n**Answer:** {answer}")

    