import asyncio
from functools import partial
import mimetypes
import time
from typing import Optional, Union
import discord
from discord.ext import commands
from discord import Embed, app_commands
import base64
import hashlib
import json
import random
from io import BytesIO
import os
import ollama
import replicate
import aiohttp
from SQL.helper import Helper  # Your custom DB helper
import requests

AiCost = 1000
# Load config
config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'Keys', 'config.json')
with open(config_path, 'r') as f:
    config = json.load(f)
# print(os.getenv("REPLICATE_API_TOKEN"))

replicate_token = config.get("ReplicateToken")

# Set your API token globally so replicate.run() can pick it up
os.environ["REPLICATE_API_TOKEN"] = replicate_token

# ---------- AI Slash Command Group ----------
@discord.app_commands.allowed_installs(guilds=True, users=True)
@discord.app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)     
class AIGroup(app_commands.Group):
    image = app_commands.Group(name="image", description="Image commands")

    def __init__(self, cog: commands.Cog):
        super().__init__(name="ai", description="AI commands group")
        self.cog = cog
 # After defining all commands, set allowed contexts
    async def set_contexts(self, bot: commands.Bot):
        for command in self.walk_commands():
            command.allowed_contexts = app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
            # await bot.tree.sync()  # Push the change to Discord
            
    @image.command(name="gen", description="Generate an image using AI")
    async def gen(self, interaction: discord.Interaction, prompt: str):
        await interaction.response.defer()
        try:
            img_stream = await self.cog.generate_image(prompt)
            file = discord.File(img_stream, filename="image.png")
            embed = discord.Embed(title=prompt)
            embed.set_image(url="attachment://image.png")
            await interaction.followup.send(embed=embed, file=file)
        except Exception as e:
            await interaction.followup.send(f"❌ Failed to generate image. {e}")
            
    @image.command(name="edit", description="Edit an image using AI")
    async def edit(self, interaction: discord.Interaction, image: discord.Attachment, prompt: str):
        await interaction.response.defer()
        try:
            image_url = await self.cog.generate_image_to_image(image.url, prompt)
            print(image_url)
            # Step 1: Download the image
            data = self.cog.download_with_retries(image_url)

            # Step 2: Wrap image bytes into BytesIO
            image_bytes = BytesIO(data)
            image_bytes.seek(0)

            # Step 3: Create the file object
            file = discord.File(fp=image_bytes, filename="image.png")

            embed = discord.Embed(title=prompt)
            embed.set_image(url="attachment://image.png")
            # embed.set_thumbnail(image.url)
            await interaction.followup.send(embed=embed, file=file)
        except Exception as e:
            await interaction.followup.send(f"❌ Failed to generate image. {e}")

    @app_commands.command(name="text", description="Generate text using AI")
    async def text(self, interaction: discord.Interaction, prompt: str, image: discord.Attachment = None):
        await interaction.response.defer()
        try:
            image_data = await self.cog.encode_image(image.url) if image else None
            result = await self.cog.generate_text(prompt=prompt, image_url=image_data)
        except Exception as e:
            result = f"❌ Error: {e}"

        # Build embed
        embed = Embed(
            description=result[:4000],  # Embed description max is 4096 chars
        )
        
        if image:
            embed.set_image(url=image.url)
            embed.set_footer(text=f"Image sent by {interaction.user.name}")

        await interaction.followup.send(embed=embed)

    @app_commands.command(name="random", description="Generate a random image with FLUX.1")
    async def random_image(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            prompt = await self.cog.generate_text("generate just a random prompt for an AI image generator. return only the prompt, no quotes.")
            hash_id = hashlib.sha256(prompt.encode()).digest()
            short_id = base64.urlsafe_b64encode(hash_id).decode()[:10]
            self.cog._db.save_prompt(short_id, base64.b64encode(prompt.encode()).decode())

            img_stream = await self.cog.generate_image(prompt)
            file = discord.File(img_stream, filename="random_image.png")
            embed = discord.Embed(title="Random Image", description=prompt)
            embed.set_image(url="attachment://random_image.png")
            await interaction.followup.send(embed=embed, file=file)
        except Exception as e:
            await interaction.followup.send(f"❌ Failed to generate random image: {e}")

    @app_commands.command(name="characters", description="See the list of AI characters you've created.")
    async def list_characters(self, interaction: discord.Interaction):
        await interaction.response.defer()

        all_characters = self.cog._db.get_girl(interaction.user.id)
        if not all_characters:
            await interaction.followup.send("You haven't created any AI characters yet. Use `/ai create` to get started!")
            return

        description = "\n".join(f"**{i+1}.** {girl[0]}" for i, girl in enumerate(all_characters))
        embed = discord.Embed(
            title="🤖 Your AI Characters",
            description=description,
            color=discord.Color.purple()
        ).set_footer(text=f"Total: {len(all_characters)} character{'s' if len(all_characters) != 1 else ''}")

        await interaction.followup.send(embed=embed)

    @app_commands.command(name="create", description=f"Create a new AI character for ${AiCost:,}")
    async def create_character(self, interaction: discord.Interaction, prompt: str = None, name: str = None):
        await interaction.response.defer()

        if self.cog._db.get_money(interaction.user.id) >= AiCost:
            await interaction.followup.send("Generating your AI character...")

            ai_prompt = await self.cog.generate_text(
                f"Generate a short random AI image prompt for a dating sim character: {name or ''} {prompt or ''}."
                f"Make sure the image is generated in hand drawn retro 90s anime art style, like evangelion."
                f" Return only the prompt, unformatted, no quotes."
            )
            print(f"create ai_prompt:\n'{ai_prompt}'\n")
            await interaction.edit_original_response(content=ai_prompt)

            img_stream = await self.cog.generate_image(ai_prompt)
            image_bytes = img_stream.read()
            image_stream = BytesIO(image_bytes)

            temp_msg = await interaction.followup.send(file=discord.File(image_stream, filename="ai_character.png"))
            image_url = temp_msg.attachments[0].url
            image_url_saved = image_url
            image_data = await self.cog.encode_image(image_url)

            character_name = name or await self.cog.generate_text(f"Generate a full name for this character: {ai_prompt}." 
                                                                f"Only return the name, no quotations, nothing else.", 
                                                                image_data)
            await interaction.edit_original_response(content=character_name)

            info = await self.cog.generate_text(f"Describe this character, give them a short biography under 500 characters based on this image." 
                                                f"include full name (must contain {character_name}), age (at least 18), gender, profession, hobbies, personality, background", 
                                                image_data)
            await interaction.edit_original_response(content=info)
            
            greeting = await self.cog.generate_text(
                f"You are roleplaying as {character_name}. Generate a short greeting under 300 characters.", 
                image_data
            )
            await interaction.edit_original_response(content=greeting)

            # print(f"create info:\n{info}\n")

            self.cog._db.save_girl(interaction.user.id, character_name, base64.b64encode(info.encode()).decode(), image_url_saved)
            self.cog._db.save_money(interaction.user.id, -AiCost)

            embed = discord.Embed(title=character_name, description=greeting[:300], color=discord.Color.magenta())
            embed.set_image(url=image_url_saved)

            await interaction.edit_original_response(content="", embed=embed)
            await temp_msg.delete()

        else:
            return await interaction.followup.send(f"❌ You only have ${self.cog._db.get_money(interaction.user.id):.2f}!", ephemeral=True)
        
    @app_commands.command(name="update", description="Update an AI character's name, info, or image.")
    async def update_character(
        self,
        interaction: discord.Interaction,
        name: str,
        new_name: Optional[str] = None,
        new_info: Optional[str] = None,
        new_image: Optional[discord.Attachment] = None,
    ):
        await interaction.response.defer()

        # Fetch all characters
        all_characters = self.cog._db.get_girl(interaction.user.id)
        if not all_characters:
            await interaction.followup.send("You haven't created any AI characters yet.")
            return

        # Find character by old name (case-insensitive partial match)
        matched_char = next((c for c in all_characters if name.lower() in c[0].lower()), None)
        if not matched_char:
            await interaction.followup.send(f"No character found matching **{name}**.")
            return

        current_name, current_info_b64, current_image_url = matched_char
        updated_name = new_name or current_name
        raw_info = new_info.replace("\\n", "\n") if new_info else base64.b64decode(current_info_b64).decode("utf-8")
        updated_info = base64.b64encode(raw_info.encode("utf-8")).decode("utf-8")
        updated_image_url = new_image.url if new_image else current_image_url

        # Delete the old character and insert the updated one
        self.cog._db.delete_girl(interaction.user.id, current_name)
        self.cog._db.save_girl(interaction.user.id, updated_name, updated_info, updated_image_url)

        await interaction.followup.send(
            f"✅ Updated character **{current_name}**.\n"
            f"New name: **{updated_name}**\n"
            f"New image: {'✅ Updated' if new_image else '❌ Unchanged'}\n"
            f"New info: {'✅ Updated' if new_info else '❌ Unchanged'}"
        )
    @app_commands.command(name="info", description="Get the info/backstory of an AI character.")
    async def get_character_info(self, interaction: discord.Interaction, index: int):
        await interaction.response.defer()

        all_characters = self.cog._db.get_girl(interaction.user.id)
        if not all_characters:
            await interaction.followup.send("You haven't created any AI characters yet.")
            return

        # Validate index (user input starts at 1, Python list is 0-based)
        if index < 1 or index > len(all_characters):
            await interaction.followup.send(f"Invalid index. You have {len(all_characters)} character(s).")
            return

        character_name, encoded_info, image_url = all_characters[index - 1]
        
        try:
            decoded_info = base64.b64decode(encoded_info).decode("utf-8")
        except Exception:
            decoded_info = "*Failed to decode character info.*"

        embed = discord.Embed(
            title=f"📖 Info: {character_name}",
            description=decoded_info if len(decoded_info) <= 4096 else decoded_info[:4093] + "...",
            color=discord.Color.blurple()
        )

        if image_url:
            embed.set_thumbnail(url=image_url)

        await interaction.followup.send(embed=embed)


    @app_commands.command(name="delete", description="Delete an AI character by its number in your list.")
    async def delete_character(self, interaction: discord.Interaction, index: int):
        await interaction.response.defer()

        all_characters = self.cog._db.get_girl(interaction.user.id)
        if not all_characters:
            await interaction.followup.send("You don't have any AI characters to delete.")
            return

        if index < 1 or index > len(all_characters):
            await interaction.followup.send(f"Invalid number. Choose a number between 1 and {len(all_characters)}.")
            return

        # Get the name of the character to delete using the index
        character_name = all_characters[index - 1][0]  # Assuming tuple format (name, desc, img)

        self.cog._db.delete_girl(interaction.user.id, character_name)

        await interaction.followup.send(f"❌ Deleted character **{character_name}** from your list.")


    @app_commands.command(name="talk", description="Talk to one of your AI characters.")
    async def talk_to_character(self, interaction: discord.Interaction, name: str, prompt: str, image: discord.Attachment = None):
        await interaction.response.defer()
            
        # Get all characters for the user
        all_characters = self.cog._db.get_girl(interaction.user.id)
        if not all_characters:
            await interaction.followup.send("You haven't created any AI characters yet. Try `/ai create` first.")
            return
        
        # Find the character by name (case-insensitive partial match)
        matched_char = next((c for c in all_characters if name.lower() in c[0].lower()), None)
        if not matched_char:
            await interaction.followup.send(f"No character found matching **{name}**. Use `/ai characters` to see your characters.")
            return
        
        # Decode the stored info
        character_name = matched_char[0]
        info = base64.b64decode(matched_char[1]).decode("utf-8")
        character_image_url = matched_char[2]
        print(f"talk name: {name}\ntalk info: {info}\ntalk img: {character_image_url}\n")


        # User's optional image URL
        user_image_url = image.url if image else None
        image_data = await self.cog.encode_image(user_image_url) if user_image_url else ""

        # Generate AI response
        reply = await self.cog.generate_text(
            f"You are roleplaying as this character: {info} (image attached). "
            f"Given the user said, '{prompt}', generate a unique reply in character. "
            f"Do not repeat the user’s words, and return only your response.",
            image_data
            )
        print(f"reply: \n{reply}\n")
        # Truncate reply if too long
        if len(reply) > 4096:
            reply = reply[:4093] + "..."
        
        # Build embed
        embed = discord.Embed(title=character_name, description=reply, color=discord.Color.magenta())
        embed.set_image(url=character_image_url)
        if user_image_url:
            embed.set_thumbnail(url=user_image_url)
        await interaction.followup.send(embed=embed)

# ---------- AI Cog ----------
class AICommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._db = Helper()
        # self.hugging_key = openai_key
        # self.replicate_token = config.get("ReplicateToken")

    async def cog_load(self):
        group = AIGroup(self)
        await group.set_contexts(self.bot)
        self.bot.tree.add_command(group)

    async def generate_image(self, prompt: str):
        output = replicate.run(
            "black-forest-labs/flux-schnell",
            input={
                "prompt": str(prompt),
                "go_fast": True,
                "megapixels": "1",
                "num_outputs": 1,
                "aspect_ratio": "1:1",
                "output_format": "png",
                "output_quality": 80,
                "num_inference_steps": 4,
                "disable_safety_checker": True
            }
        )

         # `output` is a generator of FileOutput objects
        outputs = list(output)
        if not outputs or not hasattr(outputs[0], "read"):
            raise Exception(f"❌ Unexpected output type from Replicate: {outputs}")

        # Read the file bytes from the FileOutput object
        file_output = outputs[0]
        image_bytes = file_output.read()

        return BytesIO(image_bytes)
    
    async def generate_image_to_image(self, image: str, prompt: str):   
        input = {
            "prompt": prompt,
            # "go_fast": True,
            "img_cond_path": image,
            "aspect_ratio": "match_input_image",
            "output_format": "png",
            "disable_safety_checker": True
            }


        prediction = replicate.predictions.create(
            version = "9186720586f2b98dc043280ad11e590eae7788c013d7db977ffe9192e5ae7ef4",
            input=input
        )
        print(prediction)
        while prediction.status not in ["succeeded", "failed", "canceled"]:
            time.sleep(1)
            prediction = replicate.predictions.get(prediction.id)

        if prediction.status != "succeeded":
            prediction.cancel()
            raise Exception(f"❌ Unexpected output type from Replicate")

        return prediction.output
    
    def download_with_retries(self, url, retries=3, delay=2):
        for i in range(retries):
            try:
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                return response.content
            except requests.RequestException as e:
                if i < retries - 1:
                    time.sleep(delay)
                else:
                    raise e
                
    def find_character_by_name(all_characters, search_name):
        search_name_lower = search_name.lower()
        for character in all_characters:
            if search_name_lower in character["name"].lower():
                return character
        return None
        
    async def generate_text(self, prompt: str, image_url: str=None):
        # Prepare the messages list
        messages = [{
            'role': 'user',
            'content': prompt
        }]

        # Only include images if one is provided
        if image_url:
            # print(image_url)
            messages[0]['images'] = [image_url]

        # Call the chat function
        response = ollama.chat(
            model='gemma3',
            messages=messages
        )

        # Access the response content
        return response.message.content or "❌ No response from gemma."


    async def encode_image(self, url):
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                return base64.b64encode(await resp.read()).decode()

# ---------- Extension Setup ----------
async def setup(bot: commands.Bot):
    await bot.add_cog(AICommands(bot))
