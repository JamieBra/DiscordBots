from collections import Counter
from datetime import datetime, timedelta, timezone
from getpass import getpass
from os import environ
from random import choice, shuffle, uniform
from re import compile
from sys import maxsize
from typing import Optional

from crescent import ClassCommandProto, Client, Context, command, option
from hikari import ButtonStyle, GatewayBot, Message, TextableChannel, User
from hikari.impl import CacheSettings
from uvloop import install


def utcnow():
    return datetime.now(timezone.utc)


async def find(ctx: Context, success: str, *users: Optional[User]):
    def author(message: Message):
        return specific_users and message.author.id

    def predicate(message: Message):
        return not (message.content is None or message.author.discriminator == '0000' or message in messages or pattern.search(message.content)) and author(message) in counts

    if isinstance(ctx.channel, TextableChannel):
        start = utcnow()
        deadline = start + timedelta(minutes=15)

        content = ''
        link = None

        messages: set[Message] = set()
        counts = Counter(user and user.id for user in users if not (user and user.is_bot))
        specific_users = users[0]

        while counts and utcnow() < deadline:
            if history := await ctx.channel.fetch_history(around=uniform(ctx.channel.created_at, start)).limit(101).filter(  # type: ignore
                predicate,
                ('author.is_bot', False),
                mentions_everyone=False,
                role_mention_ids=[],
                user_mentions_ids=[],
            ):
                message = choice(history)
                link = message.make_link(ctx.guild)
                content += success.format(
                    username=message.author.username,
                    content=message.content,
                    date=message.timestamp.date()
                )
                messages.add(message)
                counts[author(message)] -= 1
                counts = +counts
        if content and len(content) <= 2000:
            return content, link
    return 'No messages found.', None


bot = GatewayBot(environ.get('DISCORD') or getpass(), cache_settings=CacheSettings(max_messages=maxsize))
client = Client(bot, command_hooks=[Context.defer])
pattern = compile(r'\n|://')


def add_users(callback: type[ClassCommandProto]):
    for i in range(1, 25):
        setattr(callback, f'user{i}', option(User, default=None))
    return callback


@client.include
@command(name='convo')
@add_users
class Convo:
    count = option(int, default=5, min_value=2, max_value=25)

    async def callback(self, ctx: Context):
        users = [v for k, v in ctx.options.items() if k != 'count']
        shuffle(users)
        content, _ = await find(ctx, '{username}: {content}\n', *users or [None] * self.count)
        await ctx.respond(content)


@client.include
@command
async def quote(ctx: Context, user: Optional[User] = None):
    content, link = await find(ctx, '"{content}" -{username}, {date}', user)

    if link:
        await ctx.respond(
            content,
            component=bot.rest.build_message_action_row().add_button(ButtonStyle.LINK, link).set_label('Original').add_to_container()
        )
    else:
        await ctx.respond(content)


install()
bot.run(check_for_updates=False)
