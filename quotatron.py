from collections import Counter
from datetime import datetime, timezone
from inspect import Parameter, isclass, signature
from os import environ
from random import choice, sample, uniform
from re import compile
from typing import Annotated, cast, get_args

import miru
import uvloop
from async_timeout import timeout
from crescent import (ClassCommandOption, ClassCommandProto, Client,
                      CommandCallbackT, Context, command, option)
from hikari import GatewayBot, Message, TextableGuildChannel, User
from miru import Button, View


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


def include_command(description: str):
    def inner(callback: CommandCallbackT | type[ClassCommandProto]):
        if isclass(callback):
            callback = cast('type[ClassCommandProto]', callback)
            
            func = callback.callback
            callback.callback = lambda self, ctx: func(self, ctx, *(value for name, value in ctx.options.items() if name in variadic))

            options = 26 - sum(isinstance(value, ClassCommandOption) for value in callback.__dict__.values())
            variadic: set[str] = set()
            for parameter in signature(func).parameters.values():
                if parameter.kind is Parameter.VAR_POSITIONAL:
                    for i in range(1, options):
                        name = f'{parameter.name}{i}'
                        variadic.add(name)
                        setattr(callback, name, option(*get_args(parameter.annotation), default=None))
                    break
        return client.include(command(description=description)(callback))
    return inner


bot = GatewayBot(environ.get('DISCORD', ''))
client = Client(bot, command_hooks=[Context.defer])
pattern = compile(r'\n|://')


@include_command('Quote any number of people.')
class convo:
    count = option(int, 'How many?', default=5, min_value=2, max_value=25)

    async def callback(self, ctx: Context, *users: Annotated[User, 'Quote whom?']):
        content, _ = await find(ctx, '{username}: {content}\n', *sample(users, len(users)) or [None] * self.count)
        await ctx.respond(content)


@include_command('Quote a single person.')
async def quote(ctx: Context, user: Annotated[User | None, 'Quote whom?'] = None):
    content, link = await find(ctx, '"{content}" -{username}, {date}', user)
    view = View()
    if link:
        view.add_item(Button(label='Original', url=link))
    await ctx.respond(content, components=view)


miru.install(bot)
uvloop.install()
bot.run(check_for_updates=False)
