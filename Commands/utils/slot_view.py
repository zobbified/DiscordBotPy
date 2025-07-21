from Main.bot import discord
import random

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