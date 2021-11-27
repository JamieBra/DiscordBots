# DiscordBots
A collection of Discord bots I've written using the [Hikari](https://github.com/hikari-py/hikari) library and on top of [Hikari Lightbulb](https://github.com/tandemdude/hikari-lightbulb).

The following bots are currently a part of this repo:
* [scheduler.py](scheduler.py): Schedules a message to be sent in any channel at any time as well as the ability to easily cancel each.
* [quotatron.py](quotatron.py): Quotes up to 5 people at random in a channel as well as links to the original message.

Both bots are built using [utils.py](utils.py) which is an implementation of Lightbulb's [BotApp](https://hikari-lightbulb.readthedocs.io/en/latest/api_references/app.html#lightbulb.app.BotApp) adding in a number of convenience functions for the bots. For example, it automatically adds slash commands to the bot using one annotation and function parameter annotations. It also makes it much easier to create and listen for button presses.
