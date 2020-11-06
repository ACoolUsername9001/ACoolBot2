import json
import pymongo
from discord.ext import commands
import copy

from hooks import *

import discord


class ACoolBot(discord.Client):

    def __init__(self, **options):
        super().__init__(**options)
        self.mongo_client = pymongo.MongoClient("mongodb://localhost:27017/")

    def get_data(self, guid: str, category: str, default):
        result = list(self.mongo_client[guid][category].find())
        if not result:
            return default
        return result

    def set_data(self, guid: str, category: str, name: str, val):
        self.mongo_client[guid][category].insert_one({name: val})

    async def on_ready(self):
        await self.change_presence(activity=discord.Activity(type=discord.ActivityType.watching,
                                                             name="something"))

    async def on_message(self, message: discord.Message):
        if message.author == self.user:
            return
        if message.guild:
            hook_list = self.get_data(str(message.guild.id), 'on_message', [])
            await HooksManager.handle_hooks('on_message', hook_list, message=message)

    async def on_raw_message_edit(self, payload: discord.RawMessageUpdateEvent):
        before = None
        if hasattr(payload, 'cached_message') and payload.cached_message:
            before = payload.cached_message
        channel = self.get_channel(payload.channel_id)
        state = self._get_state()
        data = payload.data.copy()

        if 'attachments' not in data:
            data['attachments'] = []

        if 'edited_timestamp' not in data:
            return
        if before:
            after = copy.copy(before)
            after._update(payload.data)
        else:
            after = discord.Message(state=state, channel=channel, data=data)
        if after.guild:
            hook_list = self.get_data(str(after.guild.id), 'on_message_edit', [])
            await HooksManager.handle_hooks('on_message_edit', hook_list, before=before, after=after)

    @commands.command('guid')
    async def guid(self, ctx):
        await ctx.send(ctx.guild.id)


if __name__ == '__main__':
    intents = discord.Intents.default()
    intents.typing = False
    intents.presences = False
    intents.bans = False
    intents.members = True

    bot = ACoolBot(intents=intents, max_messages=4000)
    key = json.load(open('DiscordKey.json'))
    bot.run(key["key"])
