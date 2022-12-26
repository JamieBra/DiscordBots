from os import environ
from async_timeout import timeout
from asyncio import TimeoutError
from datetime import datetime, timedelta, timezone
from crescent import Bot, Context, command, option
from hikari import ButtonStyle, Member, UNDEFINED, Message, TextableChannel, User
from random import choice, shuffle, uniform
from uvloop import install


async def find(ctx: Context, success: str, failure: str, *users: User):
    def predicate(m: Message):
        return m.content and not (m.mentions_everyone or m.role_mention_ids or m.user_mentions_ids) and m.content not in messages and '://' not in m.content

    channel: TextableChannel = ctx.channel
    attrs = dict(attachments=[], embeds=[], stickers=[])
    link = None
    a = datetime.now(timezone.utc)

    try:
        async with timeout(900) as to:
            content = ''
            messages = set()
            for i, user in enumerate(users):
                predicates = [predicate]
                if isinstance(user, Member):
                    b = max(channel.created_at, user.joined_at)
                    attrs['author'] = user.user
                else:
                    b = channel.created_at
                    predicates.append(
                        lambda m: not m.author.is_bot and m.author.discriminator != '0000')

                until = timedelta(
                    seconds=(to.deadline - to._loop.time()) / (len(users) - i)) + datetime.now()
                while datetime.now() < until:
                    if history := await channel.fetch_history(around=uniform(a, b)).limit(101).filter(*predicates, **attrs):
                        m = choice(history)
                        link = m.make_link(ctx.guild)
                        messages.add(m)
                        content += success.format(username=m.author.username, content=m.content.replace(
                            '\n', ' \\ '), date=m.timestamp.date())
                        break
            if len(content) <= 2000:
                return content or failure, link
    except TimeoutError:
        return 'All attempts at finding quotes exceeded the maximum length.', None


def add_users(callback):
    for i in range(1, 25):
        setattr(callback, f'user{i}', option(User, default=None))
    return callback


bot = Bot(environ.get('DISCORD'), default_guild=581657201123262491,
          command_hooks=[Context.defer])


@ bot.include
@ command(name='convo')
@ add_users
class Convo:
    count = option(int, default=5)

    async def callback(self, ctx: Context):
        users = [v for k, v in ctx.options.items() if k != 'count']
        shuffle(users)
        content, _ = await find(ctx, '{username}: {content}\n', 'No messages found.', *users or [None] * min(self.count, 100))
        await ctx.respond(content)


@ bot.include
@ command
async def quote(ctx: Context, user: User = None):
    content, link = await find(ctx, '"{content}" -{username}, {date}', 'No message found.', user)

    if link:
        component = bot.rest.build_message_action_row().add_button(
            ButtonStyle.LINK, link).set_label('Original').add_to_container()
    else:
        component = UNDEFINED
    await ctx.respond(content, component=component)

install()
bot.run()
