import os
import json
import requests

class ChampionData:
    def __init__(self, base_path="assets/champions"):
        self.base_path = base_path
        os.makedirs(self.base_path, exist_ok=True)

        # Champion files
        self.patch_file = os.path.join("assets", "cached_patch.json")
        self.champion_json_path = os.path.join("assets", "champion.json")

        # Summoner spell files
        self.spell_base_path = "assets/spells"
        self.spell_json_path = os.path.join("assets", "summoner.json")
        os.makedirs(self.spell_base_path, exist_ok=True)

        # Local mappings
        self.current_patch = None
        self.id_to_name = {}            # champion key -> champion name
        self.spell_id_to_filename = {}  # spellId -> filename

        # Load everything
        self.load()

    # ---------------- PATCH + CHAMPIONS ----------------
    def load(self):
        latest_patch = self.fetch_latest_patch()
        cached_patch = self.get_cached_patch()

        if cached_patch != latest_patch:
            self.update_patch(latest_patch)
            self.download_champion_json(latest_patch)
            self.download_spell_json(latest_patch)

        self.load_champion_json()
        self.load_spell_json()

    def fetch_latest_patch(self):
        url = "https://ddragon.leagueoflegends.com/api/versions.json"
        try:
            r = requests.get(url, timeout=5)
            r.raise_for_status()
            return r.json()[0]
        except Exception as e:
            print("Failed to fetch latest patch:", e)
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

    # ---------------- CHAMPIONS ----------------
    def download_champion_json(self, patch):
        url = f"https://ddragon.leagueoflegends.com/cdn/{patch}/data/en_US/champion.json"
        try:
            r = requests.get(url)
            r.raise_for_status()
            with open(self.champion_json_path, "w", encoding="utf-8") as f:
                f.write(r.text)
        except Exception as e:
            print("Failed to download champion.json:", e)

    def load_champion_json(self):
        if not os.path.exists(self.champion_json_path):
            return
        with open(self.champion_json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.id_to_name = {int(entry["key"]): entry["id"] for entry in data["data"].values()}

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
        try:
            r = requests.get(url)
            r.raise_for_status()
            with open(icon_path, "wb") as f:
                f.write(r.content)
            return icon_path
        except:
            return None

    # ---------------- SUMMONER SPELLS ----------------
    def download_spell_json(self, patch):
        url = f"https://ddragon.leagueoflegends.com/cdn/{patch}/data/en_US/summoner.json"
        try:
            r = requests.get(url)
            r.raise_for_status()
            data = r.json()
            with open(self.spell_json_path, "w", encoding="utf-8") as f:
                json.dump(data, f)
        except Exception as e:
            print("Failed to download summoner.json:", e)

    def load_spell_json(self):
        if not os.path.exists(self.spell_json_path):
            return

        with open(self.spell_json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.spell_id_to_filename = {}

        for spell in data["data"].values():
            id_name = spell["id"]               # e.g. "SummonerFlash"
            key = spell["key"]                 # e.g. "4" or "SummonerFlash"

            # Only use numeric keys
            if key.isdigit():
                filename = id_name + ".png"
                self.spell_id_to_filename[key] = filename


    def get_spell_icon(self, spell_id):
        spell_id = str(spell_id)
        if spell_id not in self.spell_id_to_filename:
            return None
        filename = self.spell_id_to_filename[spell_id]
        icon_path = os.path.join(self.spell_base_path, filename)
        if os.path.exists(icon_path):
            return icon_path

        patch = self.get_cached_patch()
        if not patch:
            return None
        url = f"https://ddragon.leagueoflegends.com/cdn/{patch}/img/spell/{filename}"
        try:
            r = requests.get(url)
            r.raise_for_status()
            with open(icon_path, "wb") as f:
                f.write(r.content)
            return icon_path
        except Exception as e:
            print(f"Failed to download spell icon {filename}:", e)
            return None
