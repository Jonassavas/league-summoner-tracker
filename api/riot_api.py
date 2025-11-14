# api/riot_api.py
import os
import requests
from dotenv import load_dotenv

load_dotenv()


class RiotAPI:
    def __init__(self):
        self.api_key = os.getenv("RIOT_API_KEY")
        self.headers = {
            "X-Riot-Token": self.api_key,
            "User-Agent": "league-summoner-tracker"
        }

    # ----------------------------------------------------
    # Get PUUID from Riot ID ("Name" + "Tag")
    # ----------------------------------------------------
    def get_puuid(self, name, tag):
        url = f"https://europe.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{name}/{tag}"
        resp = requests.get(url, headers=self.headers)

        if resp.status_code != 200:
            return resp.status_code, resp.json()

        data = resp.json()
        return 200, data["puuid"]

    # ----------------------------------------------------
    # Get league entries by PUUID (returns SOLO + FLEX)
    # ----------------------------------------------------
    def get_ranked_data(self, puuid):
        url = f"https://euw1.api.riotgames.com/lol/league/v4/entries/by-puuid/{puuid}"
        resp = requests.get(url, headers=self.headers)

        if resp.status_code != 200:
            return resp.status_code, resp.json()

        raw_list = resp.json()

        ranked = {
            "solo": None,
            "flex": None
        }

        for entry in raw_list:
            if entry["queueType"] == "RANKED_SOLO_5x5":
                ranked["solo"] = entry
            if entry["queueType"] == "RANKED_FLEX_SR":
                ranked["flex"] = entry

        return 200, ranked

    # ----------------------------------------------------
    # Summoner info (contains summonerLevel, profileIconId, etc.)
    # ----------------------------------------------------
    def get_summoner_info(self, name):
        url = f"https://euw1.api.riotgames.com/lol/summoner/v4/summoners/by-name/{name}"
        resp = requests.get(url, headers=self.headers)
        return resp.status_code, resp.json()
