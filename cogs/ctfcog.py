import os
from discord.ext import commands
from discord.commands import Option
from dotenv import load_dotenv
from cogs.ctfviews import CTFView, ActiveCTFView
from controllers.CTFController import CTFController

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
      with CTFController(ctx.guild.id) as ctf_controller:
         bot_info = ctf_controller.get_ctf_bot_info()
         if bot_info is not None and bot_info.ctf is not None:
            ctf = bot_info.ctf

            msg = f"```{ctf.name} CTF\n"
            for category in ctf.categories:
               msg += f"  {category.name}\n"
               for challenge in category.challenges:
                  challenge_status = "🟩" if challenge.is_done else "🟦" if challenge.is_in_progress() else "🟥"
                  msg += f"    {challenge_status} {challenge.name}\n"
            msg += "```"

            ctf_view = CTFView(self.bot, ctf)
            await ctx.respond(msg, view=ctf_view, delete_after=30)
         else:
            await ctx.respond("No active CTF", delete_after=10)

   @commands.slash_command(guild_ids=[GUILD_ID])
   async def set_active_ctf(self, ctx: commands.Context):
      await ctx.respond("CTFs", view=ActiveCTFView(self.bot, ctx.guild.id), delete_after=10)

   # /add_ctfd_ctf name:demo url:https://demo.ctfd.io user:user password:password
   @commands.slash_command(guild_ids=[GUILD_ID])
   async def add_ctfd_ctf(self, 
                          ctx: commands.Context,
                          name: Option(str, "CTF name"), 
                          url: Option(str, "CTF CTFd url"), 
                          user: Option(str, "CTF CTFd url username"), 
                          password: Option(str, "CTF CTFd url password")):
      with CTFController(ctx.guild.id) as ctf_controller:
         await ctx.defer()
         ctf = ctf_controller.ctf_from_ctfd(name, url, user, password)
         if ctf:
            await ctx.respond(f"CTF {name} added", delete_after=10)
         else:
            await ctx.respond(f"Failed to add CTF {name}", delete_after=10)

def setup(bot):
   bot.add_cog(CTFCog(bot))
