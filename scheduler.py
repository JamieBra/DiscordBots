from app import SlashBot
from datetime import datetime
from dateutil.parser import parse
from hikari import ButtonStyle, TextableGuildChannel
from lightbulb import owner_only
from lightbulb.ext.tasks import load, task

bot = SlashBot()

@bot.slash('Schedules a message to be sent... eventually.', owner_only)
async def schedule(context, channel: ('Where?', TextableGuildChannel), timestr: ('When?', str), content: ('What?', str)):
    @bot.button('Cancel', ButtonStyle.DANGER)
    async def cancel(_):
        func.cancel()
        await context.delete_last_response()

    channel = context.get_guild().get_channel(channel)
    time = parse(timestr, fuzzy=True)
    delay = time - datetime.now()

    @task(s=delay.total_seconds(), auto_start=True, max_executions=2)
    async def func():
        if func.n_executions == 2:
            await channel.send(content)
            await context.delete_last_response()

    await context.respond(f'Scheduled `{content}` to be sent in {channel.mention} at __{time}__ ({delay}).', component=cancel)

load(bot)
bot.run()
