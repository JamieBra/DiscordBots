from getpass import getpass
from hikari import ButtonStyle, InteractionCreateEvent, InteractionType
from inspect import signature
from lightbulb import add_checks, BotApp, command, CommandErrorEvent, implements, option
from lightbulb.commands import SlashCommand
from os import name

class SlashBot(BotApp):
    def __init__(self, *cmd_checks, **kwargs):
        super().__init__(getpass(), **kwargs)
        self.callbacks = {}
        self.cmd_checks = cmd_checks

        @self.listen(CommandErrorEvent)
        async def on_error(event):
            await event.context.respond(event.exception.__cause__)
            raise event.exception
            
        @self.listen(InteractionCreateEvent)
        async def on_interaction(event):
            if event.interaction.type == InteractionType.MESSAGE_COMPONENT:
                if callback := self.callbacks.pop(event.interaction.custom_id, None):
                    callback()
                await event.interaction.message.delete()

    def slash(self, description):
        def decorator(callable):
            @self.command
            @add_checks(*self.cmd_checks)
            @command(callable.__name__, description, auto_defer=True)
            @implements(SlashCommand)
            async def func(context):
                response = await callable(context, *filter(None, context.options._options.values()))
                if isinstance(response, str):
                    content, kwargs = response, {}
                else:
                    content, kwargs = response
                await context.respond(content, **kwargs)

            for name, parameter in signature(callable).parameters.items():
                if parameter.annotation != parameter.empty:
                    if parameter.kind == parameter.VAR_POSITIONAL:
                        for i in range(1, 26 - len(func.options)):
                            option(f'{name}{i}', *parameter.annotation, required=False)(func)
                    else:
                        option(name, *parameter.annotation, required=parameter.default == parameter.empty, default=parameter.default)(func)

        return decorator

    def button(self, url_or_custom_id, label, callback=None):
        style = ButtonStyle.LINK
        if callback:
            self.callbacks[url_or_custom_id] = callback
            style = ButtonStyle.DANGER
        return self.rest.build_action_row().add_button(style, url_or_custom_id).set_label(label).add_to_container()
    
    def run(self):
        if name == 'posix':
            from uvloop import install
            install()
        super().run()