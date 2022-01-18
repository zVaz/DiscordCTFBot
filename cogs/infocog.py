import discord
from discord.ext import commands, tasks
from cogs.uitls import update_channel_name, INFO_CATEGORY_NAME, ChannelIndexes
from controllers.CTFController import CTFController

class InfoCog(commands.Cog):
   def __init__(self, bot):
      self.bot = bot
      self.update_info.start()

   def find_info_category(self, guild: discord.Guild):
      for category in guild.categories:
         if category.name == INFO_CATEGORY_NAME:
            return category
      return None

   #
   # Commands
   #

   @commands.command(name='set_current_ctf')
   async def set_current_ctf(self, ctx: commands.Context, cft_name: str):
      category = self.find_info_category(ctx.guild)
      if category is not None:
         await ctx.send("The edit request might be delayed duo to rate limit of 2 channel renames/10 minutes")
         await update_channel_name(self.bot,
                                   channel_id=category.channels[ChannelIndexes.CURRENT_CTF.value].id,
                                   name=f"🥷┃Current CTF: {cft_name}",
                                   on_success_callback = lambda channel: ctx.send("Set Current CTF Done"),
                                   on_error_callback = lambda channel: ctx.send("Set Current CTF failed"))

   #
   # Tasks
   #

   @tasks.loop(seconds=600.0)
   async def update_info(self):
      for guild in self.bot.guilds:
         category = self.find_info_category(guild)
         with CTFController(guild.id) as ctf_controller:
            bot_info = ctf_controller.get_ctf_bot_info()
            if bot_info is None or bot_info.ctf is None:
               ctf_name = "None"
            else:
               ctf_name = bot_info.ctf.name
            await update_channel_name(self.bot,
                                      channel_id=category.channels[ChannelIndexes.CURRENT_CTF.value].id,
                                      name=f"🥷┃Current CTF: {ctf_name}")
         
         if category is not None:
            await update_channel_name(self.bot,
                                      channel_id=category.channels[ChannelIndexes.MEMBERS_COUNT.value].id,
                                      name="👥┃Members: ",
                                      name_postfix_callback = lambda channel: len([m for m in channel.guild.members if not m.bot]))
            
            await update_channel_name(self.bot,
                                      channel_id=category.channels[ChannelIndexes.BOTS_COUNT.value].id,
                                      name="🤖┃Bots: ",
                                      name_postfix_callback = lambda channel: len([m for m in channel.guild.members if m.bot]))

def setup(bot):
   bot.add_cog(InfoCog(bot))
