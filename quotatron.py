from datetime import datetime, timezone
from hikari import CacheSettings, Member
from random import choice, sample, uniform
from utils import SlashBot

bot = SlashBot(cache_settings=CacheSettings(max_messages=10000))

async def find(context, success, failure, *members):
    channel = context.get_channel()
    guild = context.get_guild()
    link = None
    a = datetime.now(timezone.utc)
    
    for _ in range(5):
        content = ''
        messages = set()
        for member in members:
            predicates = [lambda m: m.content and not (m.mentions.everyone or m.mentions.role_ids or m.mentions.users) and m.content not in messages and '://' not in m.content]
            attrs = dict(attachments=[], embeds=[], stickers=[])
            if member:
                b = max(channel.created_at, member.joined_at)
                attrs['author'] = member.user
            else:
                b = channel.created_at
                predicates.append(lambda m: not m.author.is_bot and m.author.discriminator != '0000')

            for _ in range(50):
                if history := await channel.fetch_history(around=uniform(a, b)).limit(101).filter(*predicates, **attrs):
                    m = choice(history)
                    link = m.make_link(guild)
                    messages.add(m)
                    content += success.format(username=m.author.username, content=m.content.replace('\n', ' \\ '), date=m.timestamp.date())
                    break
        if len(content) <= 2000:
            return content or failure, link
    return 'All attempts at finding quotes exceeded the maximum length.', None

@bot.slash('Randomly quotes members in this channel.')
async def convo(context, *members: ('Quote whom?', Member), count: ('How many?', int) = 5):
    content, _ = await find(context, '{username}: {content}\n', 'No messages found.', *sample(members, len(members)) or [None] * min(count, 100))
    await context.respond(content)

@bot.slash('Randomly quotes a member in this channel.')
async def quote(context, member: ('Quote whom?', Member) = None):
    content, link = await find(context, '"{content}" -{username}, {date}', 'No message found.', member)
    await context.respond(content, component=bot.button(link, 'Original'))

bot.run()
