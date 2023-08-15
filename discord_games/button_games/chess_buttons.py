from __future__ import annotations

from typing import Optional
import discord
from discord.ext import commands

from ..chess_game import Chess
from .wordle_buttons import WordInputButton
from ..utils import DiscordColor, DEFAULT_COLOR, BaseView


class ChessInput(discord.ui.Modal, title="Make your move"):
    def __init__(self, view: ChessView) -> None:
        super().__init__()
        self.view = view

        self.move_from = discord.ui.TextInput(
            label="from coordinate",
            style=discord.TextStyle.short,
            required=True,
            min_length=2,
            max_length=2,
        )

        self.move_to = discord.ui.TextInput(
            label="to coordinate",
            style=discord.TextStyle.short,
            required=True,
            min_length=2,
            max_length=2,
        )

        self.add_item(self.move_from)
        self.add_item(self.move_to)

    async def on_submit(self, interaction: discord.Interaction) -> discord.Message:
        game = self.view.game
        from_coord = self.move_from.value.strip().lower()
        to_coord = self.move_to.value.strip().lower()

        uci = from_coord + to_coord

        try:
            is_valid_uci = game.board.parse_uci(uci)
        except ValueError:
            is_valid_uci = False

        if not is_valid_uci:
            return await interaction.response.send_message(
    embed=discord.Embed(
        description=(
            f"<:cross:1120656618296717312> | Invalid coordinates, cannot move from `{from_coord}` to `{to_coord}`"
        ),
        color=0x2C2F33,  # You can set the color as per your preference
    ),
    ephemeral=True,
)
        else:
            await game.place_move(uci)

            if game.board.is_game_over():
                self.view.disable_all()
                embed = await game.fetch_results()
                self.view.stop()
            else:
                embed = await game.make_embed()

            return await interaction.response.edit_message(embed=embed, view=self.view)


class ChessButton(WordInputButton):
    view: ChessView

    async def callback(self, interaction: discord.Interaction) -> None:
        game = self.view.game
        if interaction.user not in (game.black, game.white):
            return await interaction.response.send_message(
    embed=discord.Embed(
        description=(
            f"<:cross:1120656618296717312> | You are not playing this game."
        ),
        color=0x2C2F33,  # You can set the color as per your preference
    ),
    ephemeral=True,
)
        else:
            if self.label == "Cancel":
    self.view.disable_all()
    await interaction.message.edit(view=self.view)
    username = interaction.user.name
    
    embed = discord.Embed(
        description=f"Game Over, Cancelled by **{username}**.",
        color=0x2C2F33,
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)
    
    return self.view.stop()
    
            else:
                if interaction.user != game.turn:
                    return await interaction.response.send_message(
    embed=discord.Embed(
        description=(
            f"<:cross:1120656618296717312> | Wait for your turn."
        ),
        color=0x2C2F33,  # You can set the color as per your preference
    ),
    ephemeral=True,
)
                else:
                    return await interaction.response.send_modal(ChessInput(self.view))


class ChessView(BaseView):
    def __init__(self, game: BetaChess, *, timeout: float) -> None:
        super().__init__(timeout=timeout)

        self.game = game

        inpbutton = ChessButton()
        inpbutton.label = "Move"

        self.add_item(inpbutton)
        self.add_item(ChessButton(cancel_button=True))


class BetaChess(Chess):
    """
    Chess(buttons) Game
    """

    async def start(
        self,
        ctx: commands.Context[commands.Bot],
        *,
        embed_color: DiscordColor = DEFAULT_COLOR,
        timeout: Optional[float] = None,
    ) -> discord.Message:
        """
        Play Chess Game

        Parameters
        ----------
        ctx : commands.Context
            the context of the invokation command
        embed_color : DiscordColor, optional
            the color of the game embed, by default DEFAULT_COLOR
        timeout : Optional[float], optional
            the timeout for the view, by default None

        Returns
        -------
        discord.Message
            returns the game message
        """
        self.embed_color = 0x01f5b6

        embed = await self.make_embed()
        self.view = ChessView(self, timeout=timeout)

        self.message = await ctx.send(embed=embed, view=self.view)

        await self.view.wait()
        return self.message
