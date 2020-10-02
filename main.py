import discord
from datetime import datetime
from discord.ext import commands


class ACoolBot(commands.Bot):
    def __init__(self, **options):
        super().__init__(self.command_prefix, **options)

    def get_data(self, guid, category, item, default):
        return []

    def set_data(self, guid: int, category: str, name: str, val):
        pass

    async def on_ready(self):
        await self.change_presence(activity=discord.Activity(type=discord.ActivityType.watching,
                                                             name="humanity withering away"))

    @staticmethod
    def command_prefix():
        return '%'

    def on_message(self, message: discord.Message):
        hooks = self.get_data(message.guild.id, 'hooks', 'on_message', [])
        for hook in hooks:
            pass

    @staticmethod
    async def execute_action(message: discord.Message, actions):
        if 'give_roles' in actions:
            roles = list(filter(lambda r: r.id in actions['give_roles'] and r not in message.author.roles, message.guild.roles))
            if roles:
                await message.author.add_roles(roles)

        if 'delete_message' in actions:
            await message.delete(delay=actions['delete_message'])

        if 'write_embed' in actions:
            action = actions['write_embed']
            channel = discord.utils.find(lambda c: c.id == action['channel'], message.guild.text_channels)
            if channel is None:
                return

            namespace = {'author': message.author,
                         'created_at': message.created_at.strftime('%y/%m/%d %H:%M:%S'),
                         'edited_at': message.edited_at.strftime('%y/%m/%d %H:%M:%S'),
                         'content': message.content,
                         'attachments': message.attachments,
                         'message_id': message.id,
                         'jump_url': message.jump_url}

            embed = action['embed']

            for field, value in embed.copy().iteritems():
                embed[field] = value.format(**namespace)

            if embed['timestamp']:
                embed['timestamp'] = datetime.strptime(embed['timestamp'], '%y/%m/%d %H:%M:%S')

            embed = discord.Embed(**embed)
            if 'footer' in action:
                embed.set_footer(**action['footer'])
            if 'image' in action:
                embed.set_image(url=action['image'])
            if 'thumbnail' in action:
                embed.set_thumbnail(url=action['thumbnail'])
            for field in action['fields']:
                embed.add_field(**field)

            await channel.send(embed=embed)
