from enum import Enum, auto

class ChannelIndexes(Enum):
   CURRENT_CTF   = 0
   MEMBERS_COUNT = auto()
   BOTS_COUNT    = auto()
   MAX           = auto()

INFO_CATEGORY_NAME = "▬▬▬▬▬ Info ▬▬▬▬▬"

async def update_channel_name(bot,
                              channel_id: int,
                              name: str,
                              name_postfix_callback = None,
                              on_success_callback = None,
                              on_error_callback = None):
   channel = bot.get_channel(channel_id)
   if channel is not None:
      postfix = ""
      if name_postfix_callback is not None:
         postfix = name_postfix_callback(channel)
      await channel.edit(name="{}{}".format(name, postfix))
      if on_success_callback is not None:
         await on_success_callback(channel)
   else:
      if on_error_callback is not None:
         await on_error_callback(channel)