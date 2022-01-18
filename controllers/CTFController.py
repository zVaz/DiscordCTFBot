from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
import models.CTFModels as CTFModels
# import importlib.resources as pkg_resources
# import data

class GuildDB():
   def __init__(self, guild_id) -> None:
      # TODO: make it work when file not found
      #with pkg_resources.path(data, 'ctf.db') as db_path:
      #   self.engine = create_engine(f'sqlite:///{db_path}')

      self.engine = create_engine(f'sqlite:///data/{guild_id}.db')
      CTFModels.Base.metadata.create_all(self.engine)
      self.session_factory = sessionmaker(bind=self.engine)
      self.scoped_db_session = scoped_session(self.session_factory)
      self.db_session = self.scoped_db_session()

class CTFController():
   guilds_dbs: dict[int, GuildDB] = {}

   def __init__(self, guild_id) -> None:
      self.guild_id = guild_id
      if guild_id not in self.guilds_dbs:
         self.guilds_dbs[guild_id] = GuildDB(guild_id)
      self.scoped_db_session = self.guilds_dbs[guild_id].scoped_db_session
      self.db_session = self.guilds_dbs[guild_id].db_session
   
   def __enter__(self):
      return self

   def __exit__(self, exc_type, exc_value, traceback):
      self.scoped_db_session.remove()

   def set_current_ctf(self, current_ctf_id) -> str:
      bot_info = self.db_session.query(CTFModels.BotInfo).one_or_none()
      if bot_info is None:
         self.db_session.add(CTFModels.BotInfo(current_ctf_id = current_ctf_id))
      else:
         bot_info.current_ctf_id = current_ctf_id
      ctf_name = "None"
      if current_ctf_id != None:
         ctf = self.db_session.query(CTFModels.CTF).filter(CTFModels.CTF.id == current_ctf_id).one_or_none()
         ctf_name = ctf.name
      self.db_session.commit()
      return ctf_name

   def get_all_ctfs(self):
      return self.db_session.query(CTFModels.CTF)

   def mark_challenge_as_done(self, category_name, challenge_name):
      bot_info = self.db_session.query(CTFModels.BotInfo).one_or_none()
      ctf = bot_info.ctf
      challenge = ctf.get_category(category_name).get_challege(challenge_name)
      challenge.is_done = True
      self.db_session.commit()

   def stop_working_on_challenge(self, category_name, challenge_name, username):
      bot_info = self.db_session.query(CTFModels.BotInfo).one_or_none()
      ctf = bot_info.ctf
      challenge = ctf.get_category(category_name).get_challege(challenge_name)
      user_found = False
      for user in challenge.users:
         if user.username == username:
            user_found = True
            break
      
      if user_found:
         challenge.users.remove(user)
         self.db_session.commit()

   def start_working_on_challenge(self, category_name, challenge_name, username, mention):
      bot_info = self.db_session.query(CTFModels.BotInfo).one_or_none()
      ctf = bot_info.ctf
      challenge = ctf.get_category(category_name).get_challege(challenge_name)
      user_found = False
      for user in challenge.users:
         if user.username == username:
            user_found = True
            break

      if not user_found:
         user = self.db_session.query(CTFModels.User).filter(CTFModels.User.username == username).one_or_none()
         if user is None:
            user = CTFModels.User(username=username, mention=mention)
         challenge.users.append(user)
         self.db_session.commit()

   def get_ctf_and_challenge(self, category_name, challenge_name):
      bot_info = self.db_session.query(CTFModels.BotInfo).one_or_none()
      ctf = bot_info.ctf
      challenge = ctf.get_category(category_name).get_challege(challenge_name)
      return (ctf, challenge)

   def get_ctf_bot_info(self):
      return self.db_session.query(CTFModels.BotInfo).one_or_none()

   def ctf_from_ctfd(self, name, url, user, password):
      return CTFModels.ctf_from_ctfd(self.db_session, name, url, user, password)