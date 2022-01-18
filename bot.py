import os
import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

class CTFBot(commands.Bot):
   def __init__(self, intents: discord.Intents):
      super().__init__(command_prefix=commands.when_mentioned_or("!"), intents = intents)

   async def on_ready(self):
      print(f"Logged in as {self.user} (ID: {self.user.id})")

def main():
   intents = discord.Intents().default()
   intents.members = True

   bot = CTFBot(intents = intents)

   bot.load_extension("cogs.infocog")
   bot.load_extension("cogs.ctfcog")

   bot.run(TOKEN)

if __name__ == "__main__":
   main()
