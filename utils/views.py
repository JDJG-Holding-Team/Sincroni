from __future__ import annotations

from typing import TYPE_CHECKING, Literal, Optional, TypedDict, Union

import discord
from discord import ui
from discord.ext.commands import Context

if TYPE_CHECKING:
    from typing_extensions import Self


class Confirm(ui.View):
    message: Union[discord.Message, discord.WebhookMessage, discord.InteractionMessage]

    def __init__(self, user_id: int, *, timeout: float = 60.0):
        super().__init__(timeout=timeout)
        self.user_id: int = user_id
        self.value: Optional[bool] = None

    def _disable_all_buttons(self) -> None:
        for child in self.children:
            if isinstance(child, ui.Button):
                child.disabled = True

    async def interaction_check(self, interaction: discord.Interaction, /) -> bool:
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This is not for you!", ephemeral=True)
            return False

        return True

    @ui.button(
        label="Yes",
        style=discord.ButtonStyle.green,
        custom_id="confirm:yes",
    )
    async def confirm_yes(self, interaction: discord.Interaction, _: ui.Button) -> None:
        self.value = True
        self.stop()
        self._disable_all_buttons()
        await interaction.response.edit_message(view=self)

    @ui.button(
        label="No",
        style=discord.ButtonStyle.red,
        custom_id="confirm:no",
    )
    async def confirm_no(self, interaction: discord.Interaction, _: ui.Button) -> None:
        self.value = False
        self.stop()
        self._disable_all_buttons()
        await interaction.response.edit_message(view=self)

    async def on_timeout(self) -> None:
        self._disable_all_buttons()
        await self.message.edit(view=self)

    @classmethod
    async def prompt(
        cls,
        ctx_interaction: Union[discord.Interaction, Context],
        *,
        user_id: int,
        content: str = "Are you sure?",
        timeout: float = 60.0,
        **kwargs,
    ) -> Self:
        view = cls(user_id, timeout=timeout)
        _kwargs = {"view": view, "content": content, **kwargs}
        if isinstance(ctx_interaction, discord.Interaction):
            if ctx_interaction.response.is_done():
                # wait=True is always True for followup.send
                view.message = await ctx_interaction.followup.send(**_kwargs, wait=True)
            else:
                await ctx_interaction.response.send_message(**_kwargs)
                view.message = await ctx_interaction.original_response()

        elif isinstance(ctx_interaction, Context):
            view.message = await ctx_interaction.send(**_kwargs)

        await view.wait()
        return view
