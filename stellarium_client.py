"""
stellarium_client.py

Talks to Stellarium's Remote Control plugin over HTTP.

SETUP REQUIRED IN STELLARIUM:
1. Open Stellarium
2. Press F2 (or go to the toolbar) -> Plugins -> Remote Control
3. Check "Load at startup", then check "Start server"
4. Restart Stellarium if it asks
5. You should now be able to visit http://localhost:8090 in a browser
   and see a control page.
"""

import requests


class StellariumClient:
    def __init__(self, host="localhost", port=8090):
        self.base_url = f"http://{host}:{port}/api"

    def get_object_info(self, name: str) -> dict:
        """
        Fetch info for a named object (e.g. "Jupiter", "Polaris", "M42").
        Returns a dict with keys including 'ra', 'dec' (in DEGREES, not hours),
        'altitude', 'azimuth', and more.
        """
        # First, tell Stellarium to select the object by name
        select_url = f"{self.base_url}/main/focus"
        resp = requests.post(select_url, data={"target": name}, timeout=5)
        resp.raise_for_status()

        # Then ask what's currently selected/focused
        info_url = f"{self.base_url}/objects/info"
        resp = requests.get(info_url, params={"format": "json"}, timeout=5)
        resp.raise_for_status()
        return resp.json()

    def set_time_now(self):
        """Reset Stellarium's simulation clock to the real current time."""
        url = f"{self.base_url}/main/time"
        requests.post(url, data={"time": "now"}, timeout=5)

    def get_status(self) -> dict:
        """Basic sanity-check call to confirm the server is reachable."""
        url = f"{self.base_url}/main/status"
        resp = requests.get(url, timeout=5)
        resp.raise_for_status()
        return resp.json()


if __name__ == "__main__":
    # Quick manual test: run `python stellarium_client.py` while
    # Stellarium is open with the Remote Control server running.
    client = StellariumClient()
    try:
        status = client.get_status()
        print("Connected to Stellarium. Server info:")
        print(status.get("location", "no location info returned"))
    except requests.exceptions.ConnectionError:
        print("Could not connect. Is Stellarium open with Remote Control server started?")
