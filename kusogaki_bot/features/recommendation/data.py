from discord import ButtonStyle, Interaction
from discord.ui import Button, View


class MediaRec:
    def __init__(
        self,
        media_id: int,
        title: str,
        score: float = 0,
        genres: list[str] = (),
        cover_url: str = None,
    ):
        self.media_id = media_id
        self.title = title
        self.score = score
        self.genres = genres
        self.cover_url = cover_url

    def __lt__(self, other):
        return self.score < other.score

    def __eq__(self, other):
        return isinstance(other, MediaRec) and other.media_id == self.media_id


class ViewRecButton(Button):
    def __init__(self):
        super().__init__(
            style=ButtonStyle.success,
            label='All Recs',
            custom_id='view_recs',
        )


class RecView(View):
    def __init__(self, rec_service, anilist_username: str, media_type: str, genre: str):
        super().__init__(timeout=60)
        self.rec_service = rec_service
        (self.add_item(ViewRecButton()),)
        self.anilist_username = anilist_username
        self.media_type = media_type
        self.genre = genre

    async def interaction_check(self, interaction: Interaction) -> bool:
        if interaction.data['custom_id'] == 'view_recs':
            embed = self.rec_service.get_all_recs_embed(
                anilist_username=self.anilist_username,
                media_type=self.media_type,
                genre=self.genre,
            )
            await interaction.response.edit_message(embed=embed, view=None)
        return True
