import discord
from discord.ext import commands
from discord import app_commands
import random
from SQL.helper import Helper
from Commands.utils.job_helper import JobView, handle_job
# ---------- Misc Slash Command Group ----------

fired_from_job = False

@discord.app_commands.allowed_installs(guilds=True, users=True)
@discord.app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
class MiscGroup(app_commands.Group):
    def __init__(self, cog: commands.Cog):
        super().__init__(name="misc", description="Miscellaneous commands group")
        self.cog = cog
        self._db = Helper()

    async def set_contexts(self, bot: commands.Bot):
        for command in self.walk_commands():
            command.allowed_contexts = app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)

    @app_commands.command(name="hello", description="Say hello!")
    async def hello(self, interaction: discord.Interaction):
        await interaction.response.send_message(f"👋 Hello, {interaction.user.display_name}!")

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

    @app_commands.command(name="speak", description="Speak with ZobbifAI using random letters")
    async def ai_speak(self, interaction: discord.Interaction, prompt: str = None):
        await interaction.response.defer()
        words = ["ing", "er", "a", "ly", "ed", "i", "es", "re", "tion", "in", "e", "con", "y", "ter", "ex", "al", "de", "com", "o", "di", "en", "an", "ty", "ry", "u", "ti", "ri", "be", "per", "to", "pro", "ac", "ad", "ar", "ers", "ment", "or", "tions", "ble", "der", "ma", "na", "si", "un", "at", "dis", "ca", "cal", "man", "ap", "po", "sion", "vi", "el", "est", "la", "lar", "pa", "ture", "for", "is", "mer", "pe", "ra", "so", "ta", "as", "col", "fi", "ful", "ger", "low", "ni", "par", "son", "tle", "day", "ny", "pen", "pre", "tive", "car", "ci", "mo", "on", "ous", "pi", "se", "ten", "tor", "ver", "ber", "can", "dy", "et", "it", "mu", "no", "ple", "cu", " the ", " be ", " to ", " of ", " and ", " a ", " in ", " that ", " have ", " I ", "", ". ", "? ", "! ", " it ", " for ", " not ", " on ", " with ", " he ", " as ", " you ", " do ", " at ", " this ", " but ", " his ", " by ", " from ", " they ", " we ", " say ", " her ", " she ", " or ", " an ", " will ", " my ", " one ", " all ", " would ", " there ", " their ", " what ", " so ", " up ", " out ", " if ", " about ", " who ", " get ", " which ", " go ", " me ", " when ", " make ", " can ", " like ", " time ", " no ", " just ", " him ", " know ", " take ", " people ", " into ", " year ", " your ", " good ", " some ", " could ", " them ", " see ", " other ", " than ", " then ", " now ", " look ", " only ", " come ", " its ", " over ", " think ", " also", " back ", " after ", " use ", " two ", " how ", " our ", " work ", " first ", " well ", " way ", " even ", " new ", " want ", " because ", " any ", " these ", " give ", " day ", " most ", " us ", " zobbify ", " mason"]
        response = "".join(random.choices(words, k=random.randint(20, 200)))
        await interaction.followup.send(response)

    @app_commands.command(name="money", description="Check how much money you have.")
    async def check_money(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            balance = self._db.get_money(interaction.user.id)
            await interaction.followup.send(f"You have ${balance:,.2f}." if balance else "You have no money.")
        except Exception as e:
            await interaction.followup.send(f"Error fetching money: {e}")

    @app_commands.command(name="slot", description="Play the slot machine with a bet!")
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

    @app_commands.command(name="job", description="Work a job and earn money!")
    async def job(self, interaction: discord.Interaction):
        await interaction.response.defer()
        await handle_job(interaction, self._db, interaction.user.id)


    @app_commands.command(name="give", description="Give money to another user.")
    @app_commands.describe(user="The user to give money to", amount="The amount to give")
    async def give_money(self, interaction: discord.Interaction, user: discord.User, amount: float):
        await interaction.response.defer()

        giver_id = interaction.user.id
        receiver_id = user.id

        if giver_id == receiver_id:
            return await interaction.followup.send("❌ You can't give money to yourself.", ephemeral=True)
        if amount <= 0:
            return await interaction.followup.send("❌ Amount must be greater than 0.", ephemeral=True)

        giver_balance = self._db.get_money(giver_id)
        if giver_balance < amount:
            return await interaction.followup.send(f"❌ You only have ${giver_balance:.2f}!", ephemeral=True)

        # Transfer the money
        self._db.save_money(giver_id, -amount)
        self._db.save_money(receiver_id, amount)

        embed = discord.Embed(
            title="💸 Money Sent!",
            description=f"{interaction.user.mention} gave {user.mention} **${amount:.2f}**!",
            color=discord.Color.green()
        )
        await interaction.followup.send(embed=embed)
# ---------- Misc Cog ----------
class MiscCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def cog_load(self):
        group = MiscGroup(self)
        await group.set_contexts(self.bot)
        self.bot.tree.add_command(group)

# ---------- Slot Cog -----------
class SlotView(discord.ui.View):
    SYMBOLS = ["🍒", "🍋", "🍊", "🍉", "🔔", "⭐", "7️⃣"]

    def __init__(self, db, user_id, bet):
        super().__init__(timeout=60)
        self.db = db
        self.user_id = user_id
        self.bet = bet

    @staticmethod
    def evaluate(reels, bet):
        if reels[0] == reels[1] == reels[2]:
            return bet * 10, f"🎉 **JACKPOT!**\n{' '.join(reels)}\nYou won ${bet * 10:.2f}!"
        elif len(set(reels)) == 2:
            return bet * 2, f"✨ **Nice!**\n{' '.join(reels)}\nYou won ${bet * 2:.2f}!"
        else:
            return -bet, f"💸 **You lost!**\n{' '.join(reels)}\nYou lost ${bet:.2f}."

    @discord.ui.button(label="🔁 Respin", style=discord.ButtonStyle.primary)
    async def respin(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message("❌ Only the original player can respin.", ephemeral=True)

        balance = self.db.get_money(self.user_id)
        if balance < self.bet:
            return await interaction.response.send_message(f"❌ Not enough balance! You have ${balance:.2f}.", ephemeral=True)

        result = [random.choice(self.SYMBOLS) for _ in range(3)]
        payout, result_msg = self.evaluate(result, self.bet)

        self.db.save_money(self.user_id, payout)
        new_balance = self.db.get_money(self.user_id)

        embed = discord.Embed(
            title="🎰 Slot Machine - Respin",
            description=f"{result_msg}\n💰 **New Balance:** ${new_balance:.2f}",
            color=discord.Color.green() if payout > 0 else discord.Color.red()
        )
        await interaction.response.edit_message(embed=embed, view=self)
# ---------- Extension Setup ----------
async def setup(bot: commands.Bot):
    await bot.add_cog(MiscCommands(bot))
