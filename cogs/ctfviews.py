import discord
from discord.ext import commands
import models.CTFModels as CTFModels
from controllers.CTFController import CTFController
import json

def get_challenge_msg(challenge_dict: dict[str, str], bot: commands.Bot, guild_id: int):
   with CTFController(guild_id) as ctf_controller:
      ctf, challenge = ctf_controller.get_ctf_and_challenge(challenge_dict["category"], challenge_dict["challenge"])

      msg = f"{challenge.name}\n"
      msg += f"   `Points : {challenge.points}`\n"
      msg += f"   `Status : {'🟩 Done' if challenge.is_done else '🟦 In Progress' if challenge.is_in_progress() else '🟥 Not Started'}`\n"
      msg += f"   `Members: `{', '.join ([user.mention for user in challenge.users])}\n"

      cb = ChallengeButtons(bot, ctf, challenge_dict)
   return (msg, cb)

class CTFView(discord.ui.View):
    def __init__(self, bot: commands.Bot, ctf: CTFModels.CTF):
      super().__init__()
      self.bot = bot
      self.ctf = ctf
      self.message = None

      self.add_item(CTFDropdown(self.bot, ctf, self))

class ChallengeButton(discord.ui.Button):
   def __init__(self, label, style, on_click_callback):
      super().__init__(style=style, label=label)
      self.on_click_callback = on_click_callback

   async def callback(self, interaction: discord.Interaction):
      await self.on_click_callback(self,interaction)

class ChallengeButtons(discord.ui.View):
   def __init__(self, bot: commands.Bot, ctf: CTFModels.CTF, challenge_dict: dict[str, str]):
      super().__init__()
      self.bot = bot
      self.message = None
      self.challenge_dict = challenge_dict
      self.add_item(ChallengeButton(label="Start Working", style=discord.ButtonStyle.primary, on_click_callback=self.working))
      self.add_item(ChallengeButton(label="Stop Working", style=discord.ButtonStyle.red, on_click_callback=self.stop_working))
      self.add_item(ChallengeButton(label="Mark as Done", style=discord.ButtonStyle.green, on_click_callback=self.mark_as_done))

   async def working(self, button: discord.ui.Button, interaction: discord.Interaction):
      with CTFController(interaction.guild.id) as ctf_controller:
         ctf_controller.start_working_on_challenge(self.challenge_dict["category"], self.challenge_dict["challenge"], str(interaction.user), interaction.user.mention)

      msg, cb = get_challenge_msg(self.challenge_dict, self.bot, interaction.guild.id)
      await interaction.response.send_message(content=msg, delete_after=10)
      if self.message:
         await self.message.delete_original_message()
      self.stop()
   
   async def stop_working(self, button: discord.ui.Button, interaction: discord.Interaction):
      with CTFController(interaction.guild.id) as ctf_controller:
         ctf_controller.stop_working_on_challenge(self.challenge_dict["category"], self.challenge_dict["challenge"], str(interaction.user))

      msg, cb = get_challenge_msg(self.challenge_dict, self.bot, interaction.guild.id)
      await interaction.response.send_message(content=msg, delete_after=10)
      if self.message:
         await self.message.delete_original_message()
      self.stop()

   async def mark_as_done(self, button: discord.ui.Button, interaction: discord.Interaction):
      with CTFController(interaction.guild.id) as ctf_controller:
         ctf_controller.mark_challenge_as_done(self.challenge_dict["category"], self.challenge_dict["challenge"])

      msg, cb = get_challenge_msg(self.challenge_dict, self.bot, interaction.guild.id)
      await interaction.response.send_message(content=msg, delete_after=10)
      if self.message:
         await self.message.delete_original_message()
      self.stop()

class CTFDropdown(discord.ui.Select):
   def __init__(self, bot: commands.Bot, ctf: CTFModels.CTF, ctf_view: CTFView):
      self.bot = bot
      self.ctf_view = ctf_view

      options = []
      # Limit of Select is 25 SelectOptions
      for category in ctf.categories:
         for challenge in category.challenges:
            options.append(discord.SelectOption(
                  label=challenge.name,
                  value= json.dumps({"category": challenge.category.name, "challenge":challenge.name}),
                  description=challenge.category.name, emoji = "🟩" if challenge.is_done else "🟦" if challenge.is_in_progress() else "🟥"
            ))

      super().__init__(
         placeholder="Choose challenge...",
         min_values=1,
         max_values=1,
         options=options,
      )

   async def callback(self, interaction: discord.Interaction):
      challenge_dict = json.loads(self.values[0])
      msg, cb = get_challenge_msg(challenge_dict, self.bot, interaction.guild.id)
      cb.message = await interaction.response.send_message(msg, view=cb, delete_after=10)
      
      # Reset Drop Down selection
      if self.ctf_view.message:
         self.disabled = True
         #await self.ctf_view.message.edit(content=self.ctf_view.ctf.name, view=self.ctf_view)
         await self.ctf_view.message.delete_original_message()

class ActiveCTFView(discord.ui.View):
    def __init__(self, bot: commands.Bot, guild_id: int):
      super().__init__()
      self.bot = bot

      self.add_item(ActiveCTFDropdown(self.bot, guild_id))

class ActiveCTFDropdown(discord.ui.Select):
   def __init__(self, bot: commands.Bot, guild_id: int):
      self.bot = bot
      options = []
      # Limit of Select is 25 SelectOptions
      options.append(discord.SelectOption(
                  label="None",
                  value="None"
            ))
      
      with CTFController(guild_id) as ctf_controller:
         for ctf in ctf_controller.get_all_ctfs():
            options.append(discord.SelectOption(
                     label=ctf.name,
                     value=ctf.id
               ))

      super().__init__(
         placeholder="Choose Active CTF...",
         min_values=1,
         max_values=1,
         options=options,
      )

   async def callback(self, interaction: discord.Interaction):
      current_ctf_id = None if self.values[0] == "None" else self.values[0]

      with CTFController(interaction.guild.id) as ctf_controller:
         ctf_name = ctf_controller.set_current_ctf(current_ctf_id)
      
      await interaction.channel.send("The edit request might be delayed duo to rate limit of 2 channel renames/10 minutes", delete_after=5)
      await self.bot.get_cog("InfoCog").update_info()
      await interaction.response.send_message(content=f"Set {ctf_name} as active CTF", delete_after=10)