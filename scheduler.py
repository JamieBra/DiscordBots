from asyncio import create_task, sleep
from datetime import datetime
from dateutil.parser import parse
from hikari import TextableGuildChannel
from lightbulb import owner_only
from utils import SlashBot

bot = SlashBot(owner_only)

async def coro(context, channel, time):
    await sleep((time - datetime.now()).total_seconds())
    await channel.send(content)
    await context.delete_last_response()

@bot.slash('Schedules a message to be sent... eventually.')
async def schedule(context, channel: ('Where?', TextableGuildChannel), timestr: ('When?', str), content: ('What?', str)):
    channel = context.get_guild().get_channel(channel)
    time = parse(timestr)
    task = create_task(coro(context, channel, time))
    await context.respond(f'Scheduled `{content}` to be sent in {channel.mention} at __{time}__.', component=bot.button(task.get_name(), 'Cancel', task.cancel))

bot.run()
