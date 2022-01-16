from faulthandler import disable
from discord.ext import commands, tasks
import discord
from discord.commands import Option
from enum import Enum, auto
import cogs.uitls as uitls
import models.CTFModels as CFTModels
import cogs.ctfviews as ctfviews

import json
from dotenv import load_dotenv
import os

# TODO
load_dotenv("../.env")
# For faster slash command update
GUILD_ID = int(os.getenv('GUILD_ID'))

class CTFCog(commands.Cog):
   def __init__(self, bot: commands.Bot):
      self.bot = bot

   #
   # Commands
   #

   @commands.slash_command(guild_ids=[GUILD_ID])
   async def status(self, ctx: commands.Context):
      db_session = self.bot.get_db_session(ctx.guild.id)
      bot_info = db_session.query(CFTModels.BotInfo).one_or_none()
      if bot_info is not None:
         ctf = bot_info.ctf

         msg = f"```{ctf.name} CTF\n"
         for category in ctf.categories:
            msg += f"  {category.name}\n"
            for challenge in category.challenges:
               challenge_status = "🟩" if challenge.is_done else "🟦" if challenge.is_in_progress() else "🟥"
               msg += f"    {challenge_status} {challenge.name}\n"
         msg += "```"

         ctf_view = ctfviews.CTFView(self.bot, ctf)
         ctf_view.message = await ctx.respond(msg, view=ctf_view)
      else:
         await ctx.respond("No active CTF")
      db_session.remove()

   @commands.slash_command(guild_ids=[GUILD_ID])
   async def set_active_ctf(self, ctx: commands.Context):
      await ctx.respond("CTFs", view=ctfviews.ActiveCTFView(self.bot, ctx.guild.id))

   # /add_ctfd_ctf name:demo url:https://demo.ctfd.io user:user password:password
   @commands.slash_command(guild_ids=[GUILD_ID])
   async def add_ctfd_ctf(self, 
                          ctx: commands.Context,
                          name: Option(str, "CTF name"), 
                          url: Option(str, "CTF CTFd url"), 
                          user: Option(str, "CTF CTFd url username"), 
                          password: Option(str, "CTF CTFd url password")):
      db_session = self.bot.get_db_session(ctx.guild.id)
      ctf = CFTModels.ctf_from_ctfd(db_session, name, url, user, password)
      if ctf:
         await ctx.respond(f"CTF {name} added")
      else:
         await ctx.respond(f"Failef to add CTF {name}")
      db_session.remove()

def setup(bot):
    bot.add_cog(CTFCog(bot))
