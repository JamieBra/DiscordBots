from collections import Counter
from datetime import datetime, timezone
from inspect import Parameter, signature
from os import environ
from random import choice, sample, uniform
from re import compile
from typing import Annotated, get_args

import miru
import uvloop
from async_timeout import timeout
from crescent import (ClassCommandOption, ClassCommandProto, Client, Context,
                      command, option)
from hikari import GatewayBot, Message, TextableGuildChannel, User
from miru import Button, View
from more_itertools import ilen


async def find(ctx: Context, success: str, *users: User | None):
    def author(message: Message):
        return specific_users and message.author.id

    async with timeout(900):
        content = ''
        link = None
        messages: set[Message] = set()

        if isinstance(ctx.channel, TextableGuildChannel):
            counts = Counter(user and user.id for user in users if not (user and user.is_bot))
            now = datetime.now(timezone.utc)
            specific_users = users[0]

            while counts:
                if history := await ctx.channel.fetch_history(around=uniform(ctx.channel.created_at, now)).limit(101).filter(  # type: ignore
                    lambda m: bool(m.content) and m.author.discriminator != '0000' and m not in messages and not pattern.search(m.content) and author(m) in counts,  # type: ignore
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


def parse_annotation(clazz: type[ClassCommandProto]):
    callback = clazz.callback
    clazz.callback = lambda self, ctx: callback(self, ctx, *filter(None, map(ctx.options.get, variadic)))

    options = 26 - ilen(filter(ClassCommandOption.__instancecheck__, clazz.__dict__.values()))
    variadic: list[str] = []
    for param in signature(callback).parameters.values():
        if param.kind is Parameter.VAR_POSITIONAL:
            for i in range(1, options):
                name = f'{param.name}{i}'
                variadic.append(name)
                setattr(clazz, name, option(*get_args(param.annotation), default=None))
            break

    return clazz


bot = GatewayBot(environ.get('DISCORD', ''))
client = Client(bot, default_guild=581657201123262491, command_hooks=[Context.defer])
pattern = compile(r'\n|://')


@client.include
@command(name='convo')
@parse_annotation
class Convo:
    count = option(int, 'How many?', default=5, min_value=2, max_value=25)

    async def callback(self, ctx: Context, *users: Annotated[User, 'Quote whom?']):
        content, _ = await find(ctx, '{username}: {content}\n', *sample(users, len(users)) or (None,) * self.count)
        await ctx.respond(content)


@client.include
@command(name='quote')
async def quote(ctx: Context, user: Annotated[User | None, 'Quote whom?'] = None):
    content, link = await find(ctx, '"{content}" -{username}, {date}', user)
    view = View()
    if link:
        view.add_item(Button(label='Original', url=link))
    await ctx.respond(content, components=view)


miru.install(bot)
uvloop.install()
bot.run(check_for_updates=False)
