import os
import requests
from dotenv import load_dotenv
import json

load_dotenv()
API_KEY = os.getenv("RIOT_API_KEY")
#PPUID= os.getenv("PPUID")
SUMMONER_NAME = "Jone"  # Only the name, no hashtag
TAG_LINE = "SWE"
REGION = "euw1"         # EUW server

headers = {"X-Riot-Token": API_KEY, "User-Agent": "league-summoner-tracker"}

url = f"https://europe.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{SUMMONER_NAME}/{TAG_LINE}"
resp = requests.get(url, headers=headers)
data = resp.json()
#print(data)
PUUID = data.get('puuid')
#print(PUUID)

url = f"https://euw1.api.riotgames.com/lol/league/v4/entries/by-puuid/{PUUID}" #?api_key={API_KEY}"
#url = f"https://{REGION}.api.riotgames.com/lol/summoner/v4/summoners/by-name/{SUMMONER_NAME}"


resp = requests.get(url, headers=headers)
data = resp.json()

with open("league_data.json", "w", encoding="utf-8") as f:
    json.dump(data, f, indent=4)

if resp.status_code != 200:
    print(f"Error fetching summoner: {data}")
else:
    print(data)


