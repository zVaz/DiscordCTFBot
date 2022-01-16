import os
import random

from discord.ext import commands, tasks
from dotenv import load_dotenv
import discord
from enum import Enum, auto

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
import models.CTFModels as CTFModels
import importlib.resources as pkg_resources
import data

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents().default()
intents.members = True

class CTFBot(commands.Bot):
   def __init__(self, intents):
      super().__init__(command_prefix=commands.when_mentioned_or("!"), intents = intents)
      
   def get_db_session(self, guild_id):
      # TODO: make it work when file not found
      #with pkg_resources.path(data, 'ctf.db') as db_path:
      #   self.engine = create_engine(f'sqlite:///{db_path}')
      self.engine = create_engine(f'sqlite:///data/{guild_id}.db')

      CTFModels.Base.metadata.create_all(self.engine)
      self.session_factory = sessionmaker(bind=self.engine)
      self.db_session = scoped_session(self.session_factory)
      return self.db_session

   async def on_ready(self):
      print(f"Logged in as {self.user} (ID: {self.user.id})")

bot = CTFBot(intents=intents)

bot.load_extension("cogs.infocog")
bot.load_extension("cogs.ctfcog")

bot.run(TOKEN)
