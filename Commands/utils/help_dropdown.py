import discord

class GenericDropdown(discord.ui.Select):
    def __init__(self, *, options, placeholder, on_select):
        super().__init__(placeholder=placeholder, min_values=1, max_values=1, options=options)
        self.on_select_callback = on_select

    async def callback(self, interaction: discord.Interaction):
        await self.on_select_callback(interaction, self.values)


class GenericDropdownView(discord.ui.View):
    def __init__(self, *, options, placeholder, on_select):
        super().__init__(timeout=None)
        self.add_item(GenericDropdown(options=options, placeholder=placeholder, on_select=on_select))