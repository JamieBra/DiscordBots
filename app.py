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

    def component(self, add_function, id=str(uuid4())):
        if not id:
            return UNDEFINED
        def decorate(callback):
            if callback:
                self.callbacks[id] = callback
            return add_function(self.rest.build_action_row(), id).add_to_container()
        return decorate

    def button(self, label, style, *args):
        decorate = self.component(lambda builder, id: builder.add_button(style, id).set_label(label), *args)
        return decorate(None) if style == ButtonStyle.LINK else decorate

    def menu(self, *labels_and_values):
        def add_options(builder, id):
            builder = builder.add_select_menu(id)
            for label, value in labels_and_values:
                builder.add_option(label, value).add_to_menu()
            return builder
        return self.component(add_options)

    def run(self):
        try:
            from uvloop import install
            install()
        finally:
            super().run(check_for_updates=False)
