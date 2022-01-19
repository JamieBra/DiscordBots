from getpass import getpass
from hikari import ButtonStyle, InteractionCreateEvent, InteractionType, UNDEFINED
from inspect import signature
from lightbulb import add_checks, BotApp, CommandErrorEvent, option
from lightbulb.ext.filament.utils import slash_command

class SlashBot(BotApp):
    def __init__(self, *cmd_checks, **kwargs):
        super().__init__(getpass(), **kwargs)
        self.callbacks = {}
        self.cmd_checks = cmd_checks

        @self.listen(CommandErrorEvent)
        async def on_error(event):
            await event.context.respond(event.exception)
            raise event.exception

        @self.listen(InteractionCreateEvent)
        async def on_interaction(event):
            if event.interaction.type == InteractionType.MESSAGE_COMPONENT:
                if callback := self.callbacks.pop(event.interaction.custom_id, None):
                    callback()
                await event.interaction.message.delete()

    def slash(self, description, *cmd_checks):
        def decorated(callable):
            @self.command
            @add_checks(*cmd_checks, *self.cmd_checks)
            @slash_command(callable.__name__.replace('_', '-'), description, auto_defer=True)
            async def func(context):
                kwargs = dict(zip(keyword_only, map(context.raw_options.pop, keyword_only)))
                await callable(context, *filter(None, context.raw_options.values()), **kwargs)

            keyword_only = []
            for name, parameter in signature(callable).parameters.items():
                if parameter.annotation != parameter.empty:
                    if parameter.kind == parameter.VAR_POSITIONAL:
                        for i in range(1, 27 - len(callable.__annotations__)):
                            option(f'{name}{i}', *parameter.annotation, required=False)(func)
                    else:
                        if parameter.kind == parameter.KEYWORD_ONLY:
                            keyword_only.append(name)
                        option(name, *parameter.annotation, required=parameter.default == parameter.empty, default=parameter.default)(func)

        return decorated

    def button(self, url_or_custom_id, label, callback=None):
        if not url_or_custom_id:
            return UNDEFINED

        style = ButtonStyle.LINK
        if callback:
            self.callbacks[url_or_custom_id] = callback
            style = ButtonStyle.DANGER
        return self.rest.build_action_row().add_button(style, url_or_custom_id).set_label(label).add_to_container()

    def run(self):
        try:
            from uvloop import install
            install()
        except:
            print('uvloop is recommended for best performance.')
        super().run()
