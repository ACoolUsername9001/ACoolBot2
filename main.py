import json
import discord
import pymongo
from datetime import datetime
from discord.ext import commands


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
        hooks = self.get_data(str(message.guild.id), 'on_message', [])
        for hook in hooks:
            if self.is_on_message_hook_triggered(message, hook):
                if 'actions' in hook:
                    namespace = \
                        {'author': str(message.author),
                         'created at': message.created_at,
                         'content': message.content,
                         'attachments': message.attachments,
                         'message id': message.id,
                         'jump url': message.jump_url,
                         'author mention': message.author.mention}
                    await self.execute_action(message, hook['actions'], namespace)

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

        after = discord.Message(state=state, channel=channel, data=data)
        if after.author.bot:
            return

        hooks = self.get_data(str(after.guild.id), 'on_message_edit', [])
        namespace = {
            "author": str(after.author),
            "before content": before.content if isinstance(before, discord.Message) else 'UNKNOWN',
            "created at": after.created_at,
            "after content": after.content,
            "before attachments": before.attachments if before else None,
            "after attachments": after.attachments,
            "edited at": after.edited_at,
            'jump url': after.jump_url,
            'author mention': after.author.mention,
            'message id': after.id
        }

        for hook in hooks:
            if self.is_on_message_edit_hook_triggered(before, after, hook):
                await self.execute_action(message=after, actions=hook['actions'], namespace=namespace)

    def is_on_message_edit_hook_triggered(self, before, after, hook):
        if 'after' in hook and not self.is_on_message_hook_triggered(after, hook['after']):
            return False
        if not before and 'before' in hook and not self.is_on_message_hook_triggered(before, hook['before']):
            return False
        return True

    @staticmethod
    async def execute_action(message: discord.Message, actions, namespace):
        if 'give_roles' in actions:
            roles = list(filter(lambda r: r.id in actions['give_roles'] and r not in message.author.roles, message.guild.roles))
            if roles:
                await message.author.add_roles(roles)

        if 'delete_message' in actions:
            await message.delete(delay=actions['delete_message'])

        if 'write_embed' in actions:
            action = actions['write_embed']
            channel = discord.utils.find(lambda c: str(c.id) == action['channel'], message.guild.text_channels)
            if channel is None:
                return

            embed = action['embed']

            for field, value in embed.copy().items():
                embed[field] = value.format(**namespace)

            if 'timestamp' in embed:
                embed['timestamp'] = datetime.strptime(embed['timestamp'], '%Y-%m-%d %H:%M:%S.%f')

            embed = discord.Embed(**embed)
            if 'footer' in action:
                embed.set_footer(**action['footer'])
            if 'image' in action:
                embed.set_image(url=action['image'])
            if 'thumbnail' in action:
                embed.set_thumbnail(url=action['thumbnail'])
            if 'fields' in action:
                for field in action['fields']:
                    embed.add_field(**field)

            await channel.send(embed=embed)

    @staticmethod
    def is_on_message_hook_triggered(message: discord.Message, hook):
        """
        :param discord.Message message:
        :param dictionary hook:
        :return:
        """
        if "contains" in hook:
            if not (any(map(lambda s: s in message.content, hook['contains'][0])) ^ hook['contains'][1]):
                return False
        if 'author' in hook:
            if not ((str(message.author.id) in hook['author'][0]) ^ hook['author'][1]):
                return False
        if 'roles' in hook:
            if not (any(map(lambda r: str(r.id) in hook['roles'][0], message.author.roles)) ^ hook['roles'][1]):
                return False
        if 'channels' in hook:
            if not ((str(message.channel.id) in hook['channels'][0]) ^ hook['channels'][1]):
                return False
        if 'attachments' in hook:
            if not ((len(message.attachments) > 0) ^ hook['attachments']):
                return False
        return True

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
