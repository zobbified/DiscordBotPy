from Main.bot import discord
from discord import Interaction, ButtonStyle, Embed
from discord.ui import View, button, Button
import random
# Keep track of fired status per user
fired_users = {}  # {user_id: bool}
current_jobs = {}  # user_id -> job dict

# Define job types
JOBS = [
    {"title": "🍔 Burger King", "pay": 15},
    {"title": "🍕 Pizza Hut", "pay": 17},
    {"title": "🌮 Taco Bell", "pay": 14.5},
    {"title": "📦 Amazon", "pay": 20},
    {"title": "☕ Starbucks", "pay": 14},
    {"title": "🏛️ The Hater Building", "pay": 100},
]

# View class with grind button
class JobView(View):
    def __init__(self, db, user_id):
        super().__init__(timeout=None)
        self.db = db
        self.user_id = user_id

    @button(label="Work 💼", style=ButtonStyle.green, custom_id="job_grind")
    async def grind_again(self, interaction: Interaction, button: Button):
        # await interaction.response.defer()  # <-- This is critical
        button.disabled = True
        original_label = button.label
        button.label = "Working... ⏳"
        await interaction.response.edit_message(view=self)
        await handle_job(interaction, self.db, self.user_id)
        button.label = original_label
# Reusable logic for working a job
async def handle_job(interaction: Interaction, db, user_id: int):
    rng = random.randint(0, 90)
    view = JobView(db, user_id)

    # Check fired status
    is_fired = fired_users.get(user_id, False)

    if not is_fired:
         # If user has no job assigned yet, pick one
        if user_id not in current_jobs:
            current_jobs[user_id] = random.choice(JOBS)

        job = current_jobs[user_id]
        if rng <= 80:
            hours = random.randint(8, 24)
            earned = job["pay"] * hours
            db.save_money(user_id, earned)

            embed = Embed(
                title=f"{job['title']} Shift Complete!",
                description=f"You worked **{hours} hours** at **${job['pay']}/hr**.\nYou earned **${earned:.2f}** 💰",
                color=discord.Color.green()
            )
        else:
            fired_users[user_id] = True
            current_jobs.pop(user_id, None)
            embed = Embed(
                title="📉 You're Fired!",
                description="You were caught slacking off. No money earned. Try again later to get rehired.",
                color=discord.Color.red()
            )
    else:
        if rng <= 40:
            fired_users[user_id] = False
            # Assign a new random job upon rehiring
            current_jobs[user_id] = random.choice(JOBS)
            job = current_jobs[user_id]
            embed = Embed(
                title="🔁 You're Rehired!",
                description=f"{job['title']} rehired you.",
                color=discord.Color.orange()
            )
        else:
            embed = Embed(
                title="🚫 Still Fired",
                description="You're still not allowed to work. Try again later.",
                color=discord.Color.dark_gray()
            )

    embed.set_footer(text=f"Requested by {interaction.user.display_name}")
    await interaction.edit_original_response(embed=embed, view=view)
