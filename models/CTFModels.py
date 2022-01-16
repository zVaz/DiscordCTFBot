from curses import resetty
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Table, Boolean, and_, ForeignKeyConstraint, UniqueConstraint
from sqlalchemy.orm import sessionmaker, relationship, backref, scoped_session
from sqlalchemy.ext.declarative import declarative_base
import importlib.resources as resources
from requests.sessions import urljoin, urlparse, Session
from bs4 import BeautifulSoup

Base = declarative_base()

challenge_user = Table(
   "challenge_user",
   Base.metadata,
   Column("challenge_id", String , ForeignKey("challenge.id"), primary_key=True),
   Column("username"    , Integer, ForeignKey("user.username"), primary_key=True),
)

class User(Base):
   __tablename__ = "user"
   username  = Column(String, primary_key=True)
   mention   = Column(String)

class Challenge(Base):
   __tablename__ = "challenge"
   id            = Column(Integer, primary_key=True)
   name          = Column(String)
   category_id   = Column(Integer, ForeignKey("category.id"))
   points        = Column(Integer)
   description   = Column(String)
   is_done       = Column(Boolean, default=False, nullable=False)
   users         = relationship(
      "User", secondary=challenge_user, backref="challenges"
   )

   __table_args__ = (UniqueConstraint('name', 'category_id', name='_challenge_category_uc'),)

   def is_in_progress(self) -> bool:
      return len(self.users) > 0

class Category(Base):
   __tablename__ = "category"
   id          = Column(Integer, primary_key=True)
   name        = Column(String)
   ctf_id      = Column(Integer, ForeignKey("ctf.id"))
   challenges  = relationship("Challenge", backref=backref("category"))

   __table_args__ = (UniqueConstraint('name', 'ctf_id', name='_category_ctf_uc'),)

   def get_challege(self, challege_name) -> Challenge:
      for challenge in self.challenges:
         if challege_name == challenge.name:
            return challenge
      return None

class CTF(Base):
   __tablename__ = "ctf"
   id         = Column(Integer, primary_key=True)
   name       = Column(String, unique=True)
   url        = Column(String)
   categories = relationship("Category", backref=backref("ctf"))

   def get_category(self, category_name) -> Category:
      for category in self.categories:
         if category_name == category.name:
            return category
      return None

class BotInfo(Base):
   __tablename__ = "botinfo"
   id             = Column(Integer, primary_key=True)
   current_ctf_id = Column(Integer, ForeignKey("ctf.id"))
   ctf            = relationship("CTF", backref=backref("botinfo", uselist=False))

# based on https://github.com/realgam3/CTFDump
def get_nonce(session, url):
   res = session.get(urljoin(url, "/login"))
   html = BeautifulSoup(res.text, 'html.parser')
   return html.find("input", {'type': 'hidden', 'name': 'nonce'}).get("value")

def ctf_from_ctfd(db_session, name, url, username, password):
   ctf = db_session.query(CTF).filter(CTF.name == name).one_or_none()

   if ctf is None:
      ctf = CTF(name=name, url=url)
      db_session.add(ctf)
      
      session = Session()
      next_url = '/challenges'
      res = session.post(
         url=urljoin(url, "/login"),
         params={'next': next_url},
         data={
               'name': username,
               'password': password,
               'nonce': get_nonce(session, url)
         }
      )
      challenges = session.get(urljoin(url, "/api/v1/challenges")).json()
      for challenge_data in challenges["data"]:
         challenge_json = session.get(urljoin(url, f"/api/v1/challenges/{challenge_data['id']}")).json()
         category_name = challenge_json["data"]["category"]
         category = db_session.query(Category).join(CTF).filter(Category.name == category_name,
                                                                CTF.id == ctf.id).one_or_none()
         if category is None:
            category = Category(name=category_name, ctf_id=ctf.id)
            db_session.add(category)
         
         challenge_name = challenge_json["data"]["name"]
         challenge = db_session.query(Challenge).join(Category).join(CTF).filter(Challenge.name == challenge_name,
                                                                                 Category.id == category.id,
                                                                                 CTF.id == ctf.id).one_or_none()
         if challenge is None:
            challenge = Challenge(name=challenge_name, 
                                       category_id=category.id, 
                                       points = challenge_json["data"]["value"], 
                                       description = challenge_json["data"]["description"])
            db_session.add(challenge)
      db_session.commit()
   return ctf
