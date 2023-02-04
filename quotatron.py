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
        return message.author if specific_users else None

    if isinstance(ctx.channel, TextableChannel):
        now = utcnow()
        deadline = now + timedelta(minutes=15)
        content = ''
        link = None
        counts = Counter(users)
        specific_users = None not in counts
        remaining = counts.total()
        messages.clear()

        while remaining and utcnow() < deadline:
            if history := await ctx.channel.fetch_history(around=uniform(ctx.channel.created_at, now)).limit(101).filter(  # type: ignore
                lambda m: not (m.content is None or m.author.discriminator == '0000' or m in messages or pattern.search(m.content)) and author(m) in counts,
                ('author.is_bot', specific_users),
                mentions_everyone=False,
                role_mention_ids=[],
                user_mentions_ids=[]
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
                remaining -= 1
        if content and len(content) <= 2000:
            return content, link
    return 'No messages found.', None


bot = GatewayBot(environ.get('DISCORD') or getpass(), cache_settings=CacheSettings(max_messages=maxsize))
client = Client(bot, default_guild=581657201123262491, command_hooks=[Context.defer])
pattern = compile(r'\n|://')
messages: set[Message] = set()


def add_users(callback: type[ClassCommandProto]):
    for i in range(1, 25):
        setattr(callback, f'user{i}', option(User, default=None))
    return callback


@client.include
@command(name='convo')
@add_users
class Convo:
    count = option(int, default=5, max_value=25)

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
