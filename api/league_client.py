# api/league_client.py
import subprocess
import json
import base64
import requests
import re

class LeagueClient:
    def __init__(self):
        self.port = None
        self.token = None

    def find_client_info(self):
        """Extract port and token from LeagueClientUx process command line."""
        try:
            result = subprocess.check_output(
                ['wmic', 'process', 'where', "name='LeagueClientUx.exe'", 'get', 'CommandLine'],
                stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL
            ).decode(errors='ignore')

            port_match = re.search(r'--app-port=([0-9]+)', result)
            token_match = re.search(r'--remoting-auth-token=([A-Za-z0-9-_]+)', result)

            if port_match and token_match:
                self.port = port_match.group(1)
                self.token = token_match.group(1)
                return True
            return False

        except Exception:
            return False

    def request(self, endpoint: str):
        """Perform an HTTPS request to the LCU API."""
        if not self.port or not self.token:
            if not self.find_client_info():
                return None, "Unable to get League client port/token"

        url = f"https://127.0.0.1:{self.port}{endpoint}"
        auth = ('riot', self.token)

        try:
            response = requests.get(url, auth=auth, verify=False)
            return response.status_code, response.json()
        except Exception as e:
            return None, str(e)

    # -----------------------
    # Champ Select Session
    # -----------------------
    def get_champ_select(self):
        return self.request("/lol-champ-select/v1/session")
