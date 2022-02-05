# DiscordBots
A collection of Discord bots written using the [Hikari](https://github.com/hikari-py/hikari) and [Lightbulb](https://github.com/tandemdude/hikari-lightbulb) libraries.

The following bots are currently a part of this repo:
* [scheduler.py](scheduler.py): Schedules cancellable messages to be sent in any channel.
* [quotatron.py](quotatron.py): Quotes any number of people at random in a channel with links to the original message.

Both bots are built using [SlashBot](app.py) which is an implementation of Lightbulb's [BotApp](https://hikari-lightbulb.readthedocs.io/en/latest/api_references/app.html#lightbulb.app.BotApp) to make registering simple and complex commands easier. For example, it automatically registers decorated methods as slash commands and function parameter annotations as options. It also makes it much easier to create and listen for button presses. [Filament](https://github.com/tandemdude/lightbulb-ext-filament) is used where possible to simplify the implementation.
