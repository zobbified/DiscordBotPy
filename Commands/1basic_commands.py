import random
import discord
from discord import Embed, app_commands
from discord.ext import commands
from Commands.utils.help_dropdown import GenericDropdownView
import SQL.helper
from Commands.utils.job_helper import handle_job
from Commands.utils.slot_view import SlotView

@discord.app_commands.allowed_installs(guilds=True, users=True)
@discord.app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
class BasicCommands(commands.Cog):
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._db = SQL.helper.Helper() 

    @discord.app_commands.allowed_installs(guilds=True, users=True)
    @discord.app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)    
    @app_commands.command(name="slots", description="Play the slot machine with a bet!")
    @app_commands.describe(bet="How much money you want to bet (or type 'all')")
    async def slot_machine(self, interaction: discord.Interaction, bet: str):
        await interaction.response.defer()
        user_id = interaction.user.id

        # Check user's balance
        balance = self._db.get_money(user_id)
        
        # Parse 'all' or numeric bet
        if bet.strip().lower() == "all":
            bet_amount = balance
        else:
            try:
                bet_amount = float(bet)
            except ValueError:
                return await interaction.followup.send("❌ Invalid bet. Please enter a number or 'all'.")

        if bet_amount <= 0:
            return await interaction.followup.send("❌ Bet must be greater than 0.")
        if balance < bet_amount:
            return await interaction.followup.send(f"❌ You don't have enough money! Your balance: ${balance:.2f}")

        # Roll reels
        result = [random.choice(SlotView.SYMBOLS) for _ in range(3)]
        payout, result_msg = SlotView.evaluate(result, bet_amount)

        # Update DB
        self._db.save_money(user_id, payout)
        new_balance = self._db.get_money(user_id)

        embed = discord.Embed(
            title="🎰 Slot Machine",
            description=f"{result_msg}\n💰 **New Balance:** ${new_balance:.2f}",
            color=discord.Color.gold()
        )
        embed.set_footer(text=f"{interaction.user.display_name}'s slots")

        view = SlotView(self._db, user_id, bet_amount)
        await interaction.followup.send(embed=embed, view=view)
        
    @discord.app_commands.allowed_installs(guilds=True, users=True)
    @discord.app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @app_commands.command(name="work", description="Work a job and earn money!")
    async def job(self, interaction: discord.Interaction):
        await interaction.response.defer()
        await handle_job(interaction, self._db, interaction.user.id)

    @discord.app_commands.allowed_installs(guilds=True, users=True)
    @discord.app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)         
    @app_commands.command(name="help", description="List all available commands.")
    async def help(self, interaction: discord.Interaction):
        embed = Embed(
            title="📖 ZobbifAI Commands",
            description="Choose a category from the dropdown below.\n**Last updated July 2025**"
        )

        async def on_select(inter: discord.Interaction, values: list[str]):
            group = values[0].lower()

            embed = Embed(
                title=f"📖 ZobbifAI Commands — {group.capitalize()}",
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
                    lines.append((f"/{path}", desc))
                return lines

            command_lines = []
            for cmd in self.bot.tree.get_commands():
                if group == "basic" and not isinstance(cmd, app_commands.Group):
                    command_lines.extend(format_command_path(cmd))
                elif group != "basic" and isinstance(cmd, app_commands.Group) and cmd.name == group:
                    command_lines.extend(format_command_path(cmd))

            for name, desc in command_lines:
                embed.add_field(name=name, value=desc, inline=False)

            await inter.response.edit_message(embed=embed, view=view)

        dropdown_options = [
            discord.SelectOption(label="Basic", description="Top-level commands"),
            discord.SelectOption(label="AI", description="AI-related commands"),
            discord.SelectOption(label="Misc", description="Miscellaneous commands"),
        ]

        view = GenericDropdownView(
            options=dropdown_options,
            placeholder="Choose a command group...",
            on_select=on_select
        )

        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    # @app_commands.command(name="ping", description="Check if the bot is alive.")
    # async def ping(self, interaction: discord.Interaction):
    #     await interaction.response.send_message("🏓 Pong!")


    @discord.app_commands.allowed_installs(guilds=True, users=True)
    @discord.app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)    
    @app_commands.command(name="about", description="Info about the bot.")
    async def about(self, interaction: discord.Interaction):
        await interaction.response.send_message("I'm a bot created by ZobbifAI. I can help you with various tasks and provide information. Use `/help` to see what I can do!")

    @discord.app_commands.allowed_installs(guilds=True, users=True)
    @discord.app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True) 
    @app_commands.command(name="hello", description="Say hello!")
    async def hello(self, interaction: discord.Interaction):
        await interaction.response.send_message(f"👋 Hello, {interaction.user.display_name}!")

    @discord.app_commands.allowed_installs(guilds=True, users=True)
    @discord.app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)         
    @app_commands.command(name="speak", description="Speak with ZobbifAI using random letters")
    async def ai_speak(self, interaction: discord.Interaction, prompt: str = None):
        await interaction.response.defer()
        if prompt:
            prompt_split = prompt.split()
            for word in prompt_split:                
                self._db.save_speak(word)
                print(f"Saved word: {word}\n")
        words = self._db.get_speak()
        response = " ".join(random.choices(words, k=random.randint(1, 50)))
        await interaction.followup.send(response)
        
    @discord.app_commands.allowed_installs(guilds=True, users=True)
    @discord.app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)        
    @app_commands.command(name="bank", description="Check how much money you have.")
    async def check_money(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            balance = self._db.get_money(interaction.user.id)
            await interaction.followup.send(f"You have ${balance:,.2f}." if balance else "You have no money.")
        except Exception as e:
            await interaction.followup.send(f"Error fetching money: {e}")  
        
    @discord.app_commands.allowed_installs(guilds=True, users=True)
    @discord.app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True) 
    @app_commands.command(name="donate", description="Give money to another user.")
    @app_commands.describe(user="The user to give money to", amount="The amount to give")
    async def give_money(self, interaction: discord.Interaction, user: discord.User, amount: float):
        await interaction.response.defer()

        giver_id = interaction.user.id
        receiver_id = user.id

        if giver_id == receiver_id:
            return await interaction.followup.send("❌ You can't give money to yourself bozo.")
        if amount <= 0:
            return await interaction.followup.send("❌ Amount must be greater than 0.", ephemeral=True)

        giver_balance = self._db.get_money(giver_id)
        if giver_balance < amount:
            return await interaction.followup.send(f"❌ You only have ${giver_balance:.2f}!")

        # Transfer the money
        self._db.save_money(giver_id, -amount)
        self._db.save_money(receiver_id, amount)

        embed = discord.Embed(
            title="💸 Money Sent!",
            description=f"{interaction.user.mention} gave {user.mention} **${amount:.2f}**!",
            color=discord.Color.green()
        )
        await interaction.followup.send(embed=embed)

        
async def setup(bot: commands.Bot):
    await bot.add_cog(BasicCommands(bot))
