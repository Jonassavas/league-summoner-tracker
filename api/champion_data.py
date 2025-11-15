import os
import json
import requests

class ChampionData:
    def __init__(self, base_path="assets/champions"):
        self.base_path = base_path
        os.makedirs(self.base_path, exist_ok=True)

        self.patch_file = os.path.join("assets", "cached_patch.json")
        self.champion_json_path = os.path.join("assets", "champion.json")

        self.current_patch = None
        self.id_to_name = {}

        self.load()

    def load(self):
        latest_patch = self.fetch_latest_patch()
        cached_patch = self.get_cached_patch()

        if cached_patch != latest_patch:
            self.update_patch(latest_patch)
            self.download_champion_json(latest_patch)

        self.load_champion_json()

    def fetch_latest_patch(self):
        url = "https://ddragon.leagueoflegends.com/api/versions.json"
        try:
            r = requests.get(url, timeout=5)
            return r.json()[0]
        except:
            return None

    def get_cached_patch(self):
        if not os.path.exists(self.patch_file):
            return None
        try:
            with open(self.patch_file, "r") as f:
                return json.load(f).get("patch")
        except:
            return None

    def update_patch(self, patch):
        self.current_patch = patch
        with open(self.patch_file, "w") as f:
            json.dump({"patch": patch}, f)

    def download_champion_json(self, patch):
        url = f"https://ddragon.leagueoflegends.com/cdn/{patch}/data/en_US/champion.json"
        r = requests.get(url)
        with open(self.champion_json_path, "w", encoding="utf-8") as f:
            f.write(r.text)

    def load_champion_json(self):
        if not os.path.exists(self.champion_json_path):
            return
        with open(self.champion_json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.id_to_name = {
            int(entry["key"]): entry["id"]
            for entry in data["data"].values()
        }

    def get_champion_name(self, champ_id):
        return self.id_to_name.get(champ_id)

    def get_champion_icon(self, champ_id):
        name = self.get_champion_name(champ_id)
        if not name:
            return None

        icon_path = os.path.join(self.base_path, f"{name}.png")
        if os.path.exists(icon_path):
            return icon_path

        patch = self.get_cached_patch()
        if not patch:
            return None

        url = f"https://ddragon.leagueoflegends.com/cdn/{patch}/img/champion/{name}.png"
        r = requests.get(url)
        if r.status_code == 200:
            with open(icon_path, "wb") as f:
                f.write(r.content)
            return icon_path

        return None