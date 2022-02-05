from getpass import getpass
from hikari import ButtonStyle, InteractionCreateEvent, InteractionType, UNDEFINED
from inspect import signature
from lightbulb import add_checks, BotApp, option
from lightbulb.ext.filament.utils import slash_command
from uuid import uuid4

class SlashBot(BotApp):
    callbacks = {}

    def __init__(self, token=None, **kwargs):
        super().__init__(token or getpass(), **kwargs)

        @self.listen(InteractionCreateEvent)
        async def on_interaction_create(event):
            if event.interaction.type == InteractionType.MESSAGE_COMPONENT and event.interaction.custom_id in self.callbacks:
                await self.callbacks[event.interaction.custom_id](event.interaction)

    def slash(self, description, *cmd_checks):
        def decorate(command):
            @self.command
            @add_checks(*cmd_checks)
            @slash_command(command.__name__.replace('_', '-'), description, auto_defer=True)
            async def cmd_like_(context):
                kwargs = dict(zip(keyword_only, map(context.raw_options.pop, keyword_only)))
                await command(context, *filter(None, context.raw_options.values()), **kwargs)

            keyword_only = []
            for name, parameter in signature(command).parameters.items():
                if parameter.annotation != parameter.empty:
                    if parameter.kind == parameter.VAR_POSITIONAL:
                        for i in range(1, 27 - len(command.__annotations__)):
                            option(f'{name}{i}', *parameter.annotation, required=False)(cmd_like_)
                    else:
                        if parameter.kind == parameter.KEYWORD_ONLY:
                            keyword_only.append(name)
                        option(name, *parameter.annotation, required=parameter.default == parameter.empty, default=parameter.default)(cmd_like_)

        return decorate

    def button(self, label, style, url_or_custom_id=str(uuid4())):
        if not url_or_custom_id:
            return UNDEFINED
        def decorate(callback):
            self.callbacks[url_or_custom_id] = callback
            return self.rest.build_action_row().add_button(style, url_or_custom_id).set_label(label).add_to_container()
        return decorate(None) if style == ButtonStyle.LINK else decorate

    def run(self):
        try:
            from uvloop import install
            install()
        finally:
            super().run(check_for_updates=False)
