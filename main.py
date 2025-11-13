import os
import requests
from dotenv import load_dotenv
import json

load_dotenv()
API_KEY = os.getenv("RIOT_API_KEY")
PPUID= os.getenv("PPUID")
print(f"API key: {API_KEY}")
SUMMONER_NAME = "Jone"  # Only the name, no hashtag
REGION = "euw1"         # EUW server

url = f"https://euw1.api.riotgames.com/lol/league/v4/entries/by-puuid/{PPUID}" #?api_key={API_KEY}"
#url = f"https://{REGION}.api.riotgames.com/lol/summoner/v4/summoners/by-name/{SUMMONER_NAME}"
headers = {"X-Riot-Token": API_KEY, "User-Agent": "my-app"}
#print(headers)

resp = requests.get(url, headers=headers)
data = resp.json()

with open("league_data.json", "w", encoding="utf-8") as f:
    json.dump(data, f, indent=4)

if resp.status_code != 200:
    print(f"Error fetching summoner: {data}")
else:
    print(data)
