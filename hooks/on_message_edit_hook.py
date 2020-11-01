import discord
from datetime import datetime

from hooks.hook_interface import HookInterface, HooksManager


@HooksManager.add_hook_handler('on_message_edit')
class OnMessageEditHook(HookInterface):

    def __init__(self, hook, before, after: discord.Message):
        super(OnMessageEditHook, self).__init__(hook)
        self._before = before
        self._after = after
        self._before_filter = hook['before'] if 'before' in hook else None
        self._after_filter = hook['after'] if 'after' in hook else None
        self._namespace = {
            "author": str(after.author),
            "before content": before.content if isinstance(before, discord.Message) else 'UNKNOWN',
            "before attachments": before.attachments if before else None,
            "created at": after.created_at,
            "after content": after.content,
            "after attachments": after.attachments,
            "edited at": after.edited_at,
            'jump url': after.jump_url,
            'author mention': after.author.mention,
            'message id': after.id
        }

    def _calculate_filter(self, message):
        for f_name, args in self._filters.items():
            if f_name in HooksManager.FILTERS[self.__class__.__name__]:
                if type(args) is not list:
                    args = [args]
                yield HooksManager.FILTERS[self.__class__.__name__][f_name](self, message, *args[0:-1]) ^ args[-1]

    def _filter(self):
        if self._before_filter:
            if self._before:
                before_result = self._calculate_filter(self._before)
            else:
                before_result = (False,)
        else:
            before_result = (True, )
        if self._after_filter:
            after_result = self._calculate_filter(self._after)
        else:
            after_result = (True,)

        return all(after_result) and all(before_result)

    @HooksManager.add_filter('contains')
    def contains(self, message: discord.Message, list_of_strings):
        """
        function logic here
        :param discord.Message message:
        :param list[str] list_of_strings:
        :return bool: True if filter is ok otherwise False
        """
        for s in list_of_strings:
            if s in message.content:
                return True
        return False

    @HooksManager.add_filter('roles')
    def has_role(self, message: discord.Message, list_of_roles):
        """

        :param discord.Message message:
        :param list[str] list_of_roles:
        :return bool:
        """
        return any(map(lambda r: str(r.id) in list_of_roles, message.author.roles))

    @HooksManager.add_filter('attachments')
    def has_attachments(self, message):
        return len(message.attachments) > 0

    @HooksManager.add_filter('channels')
    def in_channel(self, message: discord.Message, list_of_channel_ids):
        """

        :param discord.Message message:
        :param list[str] list_of_channel_ids:
        :return bool:
        """
        return str(message.channel.id) in list_of_channel_ids

    @HooksManager.add_filter('author')
    def author(self, message: discord.Message, author_id):
        """
        :param discord.Message message:
        :param list[str] author_id:
        :return bool:
        """
        return str(message.author.id) in author_id

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
        channel = discord.utils.find(lambda c: str(c.id) == channel, self._after.guild.text_channels)
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
        await self._after.delete(delay=delay)

    @HooksManager.add_action('give_roles')
    async def give_roles(self, list_of_role_ids):
        """

        :param list[str] list_of_role_ids:
        :return:
        """
        roles = list(filter(lambda r: r.id in list_of_role_ids and r not in self._after.author.roles, self._after.guild.roles))
        if roles:
            await self._after.author.add_roles(roles)

    @HooksManager.add_action('remove_roles')
    async def give_roles(self, list_of_role_ids):
        """

        :param list[str] list_of_role_ids:
        :return:
        """
        roles = list(filter(lambda r: r.id in list_of_role_ids and r not in self._after.author.roles, self._after.guild.roles))
        if roles:
            await self._after.author.remove_roles(roles)
