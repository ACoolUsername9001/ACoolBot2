import discord
from discord.ext import commands


class ACoolBot(commands.Bot):
    def __init__(self, **options):
        super().__init__(self.command_prefix, **options)

    def get_data(self, guid, item, default):
        return []

    def set_data(self, guid: int, name: str, val):
        pass

    async def on_ready(self):
        await self.change_presence(activity=discord.Activity(type=discord.ActivityType.watching,
                                                             name="humanity withering away"))

    def command_prefix(self, bot, message: discord.Message):
        if not message.guild:
            return '*'
        prefixes = self.get_data(message.guild.id, 'prefix', ['*'])
        return commands.when_mentioned_or(*prefixes)(self, message)

    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState,
                                    after: discord.VoiceState):
        await self.give_role_voice_channel(member, before, after)

    @staticmethod
    async def give_role_voice_channel(member: discord.Member, before: discord.VoiceState,
                                      after: discord.VoiceState):
        if before.channel == after.channel:
            return

        if after.channel is not None:
            if before.channel is not None:
                before_role = discord.utils.find(lambda r: r.name.lower() == before.channel.name.lower(), member.guild.roles)
            after_role = discord.utils.find(lambda r: r.name.lower() == after.channel.name.lower(), member.guild.roles)
            if after_role is None:
                after_role = discord.utils.find(lambda r: r.name.lower() == after.channel.name.lower(),
                                        after.channel.guild.roles)
            if after_role is None:
                after_role = await after.channel.guild.create_role(name=after.channel.name)
        else:
            before_role = discord.utils.find(lambda r: r.name == before.channel.name, before.channel.guild.roles)
        roles = member.roles

        if before.channel is not None:
            if before_role in roles:
                await member.remove_roles(before_role, reason='voice connectivity')

        if after.channel is not None:
            if after_role not in roles:
                await member.add_roles(after_role, reason='Voice connectivity')

    def on_message(self, message: discord.Message):
        pass
