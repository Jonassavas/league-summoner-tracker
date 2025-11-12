import os
import requests
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("RIOT_API_KEY")
SUMMONER_NAME = "Faker"
REGION = "kr"  # change to the correct region code

url = f"https://{REGION}1.api.riotgames.com/lol/summoner/v4/summoners/by-name/{SUMMONER_NAME}"
headers = {"X-Riot-Token": API_KEY}

resp = requests.get(url, headers=headers)
data = resp.json()

if resp.status_code != 200:
    print(f"Error fetching summoner: {data}")
else:
    print(f"Summoner {SUMMONER_NAME} info:")
    print(f"Level: {data.get('summonerLevel')}")
    print(f"ID: {data.get('id')}")