from discord import app_commands, Interaction
from discord.ext import commands
import discord
import base64

class DeleteButton(discord.ui.Button):
    def __init__(self, character_name, user_id, db):
        super().__init__(label="Delete Character", style=discord.ButtonStyle.danger)
        self.character_name = character_name
        self.user_id = user_id
        self.db = db

    async def callback(self, interaction: Interaction):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("You can't delete someone else's character!", ephemeral=True)
            return

        self.db.delete_girl(self.character_name)
        
        await interaction.response.send_message(f"❌ Deleted character **{self.character_name}**.", ephemeral=True)


class CharacterView(discord.ui.View):
    def __init__(self, character_name, user_id, db):
        super().__init__(timeout=None)
        self.add_item(DeleteButton(character_name, user_id, db))