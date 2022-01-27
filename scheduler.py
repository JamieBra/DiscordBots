from asyncio import create_task, sleep
from datetime import datetime
from dateutil.parser import parse
from hikari import ButtonStyle, TextableGuildChannel
from lightbulb import owner_only
from utils import SlashBot

bot = SlashBot()

async def coro(context, channel, delay, content):
    await sleep(delay.total_seconds())
    await channel.send(content)
    await context.delete_last_response()

@bot.slash('Schedules a message to be sent... eventually.', owner_only)
async def schedule(context, channel: ('Where?', TextableGuildChannel), timestr: ('When?', str), content: ('What?', str)):
    channel = context.get_guild().get_channel(channel)
    time = parse(timestr, fuzzy=True)
    delay = time - datetime.now()
    task = create_task(coro(context, channel, delay, content))
    
    @bot.button(task.get_name(), 'Cancel', ButtonStyle.DANGER)
    async def cancel(_):
        task.cancel()
        await context.delete_last_response()
    
    await context.respond(f'Scheduled `{content}` to be sent in {channel.mention} at __{time}__ ({delay}).', component=cancel)

bot.run()
