import discord
from datetime import datetime

from hooks.hook_interface import HookInterface, HooksManager


@HooksManager.add_hook_handler('on_message')
class OnMessageHook(HookInterface):

    def __init__(self, hook, message: discord.Message):
        super(OnMessageHook, self).__init__(hook)
        self._message = message
        self._filters = hook['filters']
        self._actions = hook['actions']
        self._namespace = {
            'author': str(message.author),
            'created at': message.created_at,
            'content': message.content,
            'attachments': message.attachments,
            'message id': message.id,
            'jump url': message.jump_url,
            'author mention': message.author.mention
            }

    def _filter(self):
        if self._filters:
            filters_result = (HooksManager.FILTERS[self.__class__.__name__][f_name](self, *args[0:-1] if type(args) is list else [args][0:-1]) ^ (args[-1] if type(args) is list else [args][-1]) for f_name, args in self._filters.items() if f_name in HooksManager.FILTERS[self.__class__.__name__])
        else:
            filters_result = (True,)

        return all(filters_result)

    @HooksManager.add_filter('contains')
    def contains(self, list_of_strings):
        """
        function logic here
        :param list[str] list_of_strings:
        :return bool: True if filter is ok otherwise False
        """
        for s in list_of_strings:
            if s in self._message.content:
                return True
        return False

    @HooksManager.add_filter('author')
    def author(self, author_id):
        """

        :param list[str] author_id:
        :return bool:
        """
        return str(self._message.author.id) in author_id

    @HooksManager.add_filter('roles')
    def has_role(self, list_of_roles):
        """

        :param list[str] list_of_roles:
        :return bool:
        """
        return any(map(lambda r: str(r.id) in list_of_roles, self._message.author.roles))

    @HooksManager.add_filter('attachments')
    def has_attachments(self):
        return len(self._message.attachments) > 0

    @HooksManager.add_filter('channels')
    def in_channel(self, list_of_channel_ids):
        """

        :param list[str] list_of_channel_ids:
        :return bool:
        """
        return str(self._message.channel.id) in list_of_channel_ids

    @HooksManager.add_action('write_embed')
    async def write_embed(self, channel, embed, footer=None, image=None, thumbnail=None, fields=None):
        """
        :param str channel:
        :param dict embed:
        :param dict footer:
        :param str image:
        :param str thumbnail:
        :param list[dict] fields:
        :return:
        """
        channel = discord.utils.find(lambda c: str(c.id) == channel, self._message.guild.text_channels)
        if channel is None:
            return

        for field, value in embed.copy().items():
            embed[field] = value.format(**self._namespace)

        if 'timestamp' in embed:
            embed['timestamp'] = datetime.strptime(embed['timestamp'], '%Y-%m-%d %H:%M:%S.%f')

        embed = discord.Embed(**embed)
        if footer:
            embed.set_footer(**footer)
        if image:
            embed.set_image(url=image)
        if thumbnail:
            embed.set_thumbnail(url=thumbnail)
        if fields:
            for field in fields:
                embed.add_field(**field)

        await channel.send(embed=embed)

    @HooksManager.add_action('delete_message')
    async def delete_message(self, delay):
        await self._message.delete(delay=delay)

    @HooksManager.add_action('give_roles')
    async def give_roles(self, list_of_role_ids):
        """

        :param list[str] list_of_role_ids:
        :return:
        """
        roles = list(filter(lambda r: r.id in list_of_role_ids and r not in self._message.author.roles, self._message.guild.roles))
        if roles:
            await self._message.author.add_roles(roles)

    @HooksManager.add_action('remove_roles')
    async def give_roles(self, list_of_role_ids):
        """

        :param list[str] list_of_role_ids:
        :return:
        """
        roles = list(filter(lambda r: r.id in list_of_role_ids and r not in self._message.author.roles, self._message.guild.roles))
        if roles:
            await self._message.author.remove_roles(roles)
