from discord.ext import commands
from Commands.groups.misc_group import MiscGroup

class MiscCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def cog_load(self):
        group = MiscGroup(self)
        await group.set_contexts(self.bot)
        self.bot.tree.add_command(group)

# ---------- Extension Setup ----------
async def setup(bot: commands.Bot):
    await bot.add_cog(MiscCommands(bot))
