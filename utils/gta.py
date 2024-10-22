from discord import Embed
from bs4 import BeautifulSoup
import aiohttp

from views.scroller import Scroller
from utils.general import get_embed, EmbedType
from config import GTA_SEASON

class LeaderboardEntry:
    username: str = None
    rank: int = None
    attempts: int = None
    correct_attempts: int = None
    success_percentage: int = None
    total_points: int = None
    
    def __init__(self, **kwargs):
        for i, j in kwargs.items():
            setattr(self, i, j)
            

async def fetch_html(url: str) -> str:
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response: 
            return await response.text()
             
async def get_gta_leaderboard() -> Scroller:
    
    html = await fetch_html("https://kusogaki.co/gta/{}".format(GTA_SEASON))
    
    bs = BeautifulSoup(html, "html.parser")
    
    leaderboard = bs.find("div", id="leaderboard").find_all("div")
    
    leaderboard_entries: list[LeaderboardEntry] = []
    rank_counter = 1
    
    index = 6
    
    while index < len(leaderboard):
        
        leaderboard_entries.append(LeaderboardEntry(rank=rank_counter, username=leaderboard[index + 1].text, attempts=leaderboard[index + 2].text, correct_attempts=leaderboard[index + 3].text, success_percentage=leaderboard[index + 4].text, total_points=leaderboard[index + 5].text))
        
        rank_counter = rank_counter + 1
        index = index + 6
        
    number_of_pages = len(leaderboard_entries) // 15
    extra_page = False if len(leaderboard_entries) % 15 == 0 else True
    
    leaderboard_embeds: list[Embed] = []
    
    for i in range(0, number_of_pages):
        
        embd: Embed = await get_embed(EmbedType.NORMAL, "GTA Leaderboard", "")
        embd.description = "`Rank | Username         | Percentage | Score` \n\n"
        embd.set_footer(text=f"Page {i + 1}")
        
        for i in range(15 * i, 15 * (i + 1)):
            embd.description += "`{} | {} | {} | {}`\n".format(f"{i + 1}".ljust(4, " "), leaderboard_entries[i].username.ljust(16, " "), f"{leaderboard_entries[i].success_percentage}".ljust(10, " "), f"{leaderboard_entries[i].total_points}".ljust(5, " "))
        
        if embd:
            for j in range(len(leaderboard_entries) - len(leaderboard_entries) % 15, len(leaderboard_entries)):
                embd.description += "`{} | {} | {} | {}`".format(f"{j + 1}".ljust(4, " "), leaderboard_entries[j].username.ljust(16, " "), f"{leaderboard_entries[j].success_percentage}".ljust(10, " "), f"{leaderboard_entries[j].total_points}".ljust(5, " "))
        
        leaderboard_embeds.append(embd)    
        
    # if extra_page:
    #     extra_page: Embed = await get_embed(EmbedType.NORMAL, "GTA Leaderboard", "")
    #     extra_page.description = "`Rank | Username         | Percentage | Score` \n\n"
    #     extra_page.set_footer(text=f"Page {number_of_pages + 1}")
        
    #     for j in range(len(leaderboard_entries) - len(leaderboard_entries) % 15, len(leaderboard_entries)):
    #         extra_page.description += "`{} | {} | {} | {}`".format(f"{j + 1}".ljust(4, " "), leaderboard_entries[j].username.ljust(16, " "), f"{leaderboard_entries[j].success_percentage}".ljust(10, " "), f"{leaderboard_entries[j].total_points}".ljust(5, " "))
            
    # leaderboard_embeds.append(extra_page)
    
    return Scroller(leaderboard_embeds)
    