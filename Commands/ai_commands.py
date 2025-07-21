import asyncio
import os, json
from SQL.helper import Helper
from io import BytesIO
from discord.ext import commands
import time
import base64
import ollama
import replicate
import aiohttp
import requests
import Commands.groups.ai_group as AIGroup
# import flux.demo_gr as flux
# Load config
config_path = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "Keys", "config.json"
)
with open(config_path, "r") as f:
    config = json.load(f)
# print(os.getenv("REPLICATE_API_TOKEN"))

replicate_token = config.get("ReplicateToken")

# Set your API token globally so replicate.run() can pick it up
os.environ["REPLICATE_API_TOKEN"] = replicate_token

chat_history = []
char_chat_history = []
# ---------- AI Cog ----------
class AICommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._db = Helper()

    async def cog_load(self):
        group = AIGroup.AIGroup(self)
        await group.set_contexts(self.bot)
        self.bot.tree.add_command(group)

    async def generate_image(self, prompt: str):
        output = replicate.run(
            "black-forest-labs/flux-schnell",
            input={
                "prompt": str(prompt),
                "go_fast": False,
                "megapixels": "1",
                "num_outputs": 1,
                "aspect_ratio": "1:1",
                "output_format": "jpg",
                "output_quality": 80,
                "num_inference_steps": 4,
                "disable_safety_checker": True,
            },
        )

        # `output` is a generator of FileOutput objects
        outputs = list(output)
        if not outputs or not hasattr(outputs[0], "read"):
            raise Exception(f"❌ Unexpected output type from Replicate: {outputs}")

        # Read the file bytes from the FileOutput object
        file_output = outputs[0]
        image_bytes = file_output.read()

        return BytesIO(image_bytes)
    # async def generate_audio(self, prompt: str = None):
    #     input = {
    #         "prompt": prompt or "",
    #         "model_version": "large",
    #         "save_spectrogram": False
    #     }
    #     prediction = replicate.predictions.create(
    #         version="eebfed4a1749bb1172f005f71fac5a1e0377502ec149c9d02b56ac1de3aa9f07",
    #         input=input,
    #     )
    #     print(prediction)
    #     while prediction.status not in ["succeeded", "failed", "canceled"]:
    #         time.sleep(1)
    #         prediction = replicate.predictions.get(prediction.id)

    #     if prediction.status != "succeeded":
    #         prediction.cancel()
    #         raise Exception(f"❌ Unexpected output type from Replicate")

    #     return prediction.output['wav']
            
    async def generate_image_to_image(self, image: str, prompt: str):
        input = {
            "prompt": prompt,
            # "go_fast": True,
            "img_cond_path": image,
            # "seed": random.randint(1,100000),
            "guidance": 1,
            "num_inference_steps": 20,
            "output_quality": 80,
            "aspect_ratio": "1:1",
            "speed_mode": "Extra Juiced 🔥 (more speed)",
            "output_format": "jpg",
            "disable_safety_checker": True,
        }

        prediction = replicate.predictions.create(
            version="9186720586f2b98dc043280ad11e590eae7788c013d7db977ffe9192e5ae7ef4",
            input=input,
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

    async def generate_text_char(self, prompt: str, image_url: str = None):
        # Prepare the messages list
        messages = {"role": "user", "content": f"respond to the user's prompt. stay as the same character, but act like the previous context messages were from a different character. {prompt}"}
         # Only include images if one is provided
        if image_url != None:
            # print(image_url)
            messages["images"] = [image_url]
        char_chat_history.append(messages)
        print(f"ollama prompt: {char_chat_history}")
        
        # Run the blocking function in a background thread
        response = await asyncio.to_thread(
            ollama.chat, model="huihui_ai/llama3.2-abliterate", messages=char_chat_history, stream=False, think=False, options={"thinking": False}
        )
        print (f"ollama response: {response}")
        char_chat_history.append(response.message)
        
        if len(chat_history) > 2:
            chat_history.pop(0)
            chat_history.pop(1)
        # Access the response content
        return response.message.content or "❌ No response."
    
    async def generate_text(self, prompt: str, image_url: str = None):
        # Prepare the messages list
        messages = {"role": "user", "content": prompt}
         # Only include images if one is provided
        if image_url != None:
            # print(image_url)
            messages["images"] = [image_url]
        
        chat_history.append(messages)
        print(f"ollama prompt: {chat_history}")

        # Run the blocking function in a background thread
        response = await asyncio.to_thread(
            ollama.chat, model="huihui_ai/llama3.2-abliterate", messages=chat_history, stream=False, think=False, options={"thinking": False}
        )
        print (f"ollama response: {response}")
        chat_history.append(response.message)

        if len(chat_history) > 6:
            chat_history.pop(0)
            chat_history.pop(1)

        # Access the response content
        return response.message.content or "❌ No response."
    async def encode_image(self, url):
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                return base64.b64encode(await resp.read()).decode()


# ---------- Extension Setup ----------
async def setup(bot: commands.Bot):
    await bot.add_cog(AICommands(bot))
