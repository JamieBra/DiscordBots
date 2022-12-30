from os import environ
from typing import Optional
from datetime import datetime, timedelta, timezone
from crescent import Bot, ClassCommandProto, Context, command, option
from hikari import ButtonStyle, Member, TextableChannel, User
from random import choice, shuffle, uniform
from uvloop import install


def utcnow():
    return datetime.now(timezone.utc)


async def find(ctx: Context, success: str, *users: Optional[User]):
    if isinstance(ctx.channel, TextableChannel):
        a = utcnow()
        content = ''
        count = len(users)
        deadline = a + timedelta(minutes=15)
        link = None
        messages = set()

        for i, user in enumerate(users):
            attrs = {}
            predicates = []

            if isinstance(user, Member):
                b = max(ctx.channel.created_at, user.joined_at)
                attrs['author'] = user.user
            else:
                b = ctx.channel.created_at
                predicates.append(('author.is_bot', False))

            now = utcnow()
            until = (deadline - now) / (count - i) + now
            while utcnow() < until:
                if history := await ctx.channel.fetch_history(around=uniform(a, b)).limit(101).filter(
                    lambda m: m.content is not None and m.author.discriminator != '0000' and m not in messages and '://' not in m.content,
                    *predicates,
                    mentions_everyone=False,
                    role_mention_ids=[],
                    user_mentions_ids=[],
                    **attrs
                ):
                    m = choice(history)
                    link = m.make_link(ctx.guild)
                    content += success.format(username=m.author.username, content=m.content.replace(
                        '\n', ' / '), date=m.timestamp.date()) + '\n'
                    messages.add(m)
                    break
        if content and len(content) <= 2000:
            return content, link
    return 'No messages found.', None


def add_users(callback: type[ClassCommandProto]):
    for i in range(1, 25):
        setattr(callback, f'user{i}', option(User, default=None))
    return callback


bot = Bot(environ.get('DISCORD'), command_hooks=[Context.defer])


@ bot.include
@ command(name='convo')
@ add_users
class Convo:
    count = option(int, default=5)

    async def callback(self, ctx: Context):
        users = [v for k, v in ctx.options.items() if k != 'count']
        shuffle(users)
        content, _ = await find(ctx, '{username}: {content}', *users or [None] * min(self.count, 25))
        await ctx.respond(content)


@ bot.include
@ command
async def quote(ctx: Context, user: Optional[User] = None):
    content, link = await find(ctx, '"{content}" -{username}, {date}', user)

    if link:
        await ctx.respond(content, component=bot.rest.build_message_action_row().add_button(ButtonStyle.LINK, link).set_label('Original').add_to_container())
    else:
        await ctx.respond(content)

install()
bot.run()
