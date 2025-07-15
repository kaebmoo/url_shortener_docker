import requests
from datetime import datetime, timedelta

class PhishingData:
    def __init__(self):
        self.phishing_urls = []
        self.last_update_time = datetime.min
    
    def fetch_openphish_urls(self):
        try:
            response = requests.get("https://www.openphish.com/feed.txt", timeout=10)
            response.raise_for_status()
            return response.text.splitlines()
        except requests.exceptions.Timeout:
            print("Timeout occurred while fetching the OpenPhish feed.")
        except requests.exceptions.RequestException as e:
            print(f"An error occurred with OpenPhish: {e}")
        return []

    def fetch_phishing_army_urls(self):
        try:
            response = requests.get("https://phishing.army/download/phishing_army_blocklist.txt", timeout=10)
            response.raise_for_status()
            lines = response.text.splitlines()
            # กรองบรรทัดที่ว่างเปล่าและบรรทัดที่ขึ้นต้นด้วย #
            urls = [line for line in lines if line and not line.startswith('#')]
            return urls
        except requests.exceptions.Timeout:
            print("Timeout occurred while fetching the Phishing Army feed.")
        except requests.exceptions.RequestException as e:
            print(f"An error occurred with Phishing Army: {e}")
        return []

    def fetch_phishing_urls(self):
        openphish_urls = self.fetch_openphish_urls()
        phishing_army_urls = self.fetch_phishing_army_urls()

        # รวมรายการ URL จากทั้งสองแหล่ง
        self.phishing_urls = list(set(openphish_urls + phishing_army_urls))
        self.last_update_time = datetime.now()
        print("Phishing feeds updated successfully from OpenPhish and Phishing Army.")
    
    def update_phishing_urls(self):
        if datetime.now() - self.last_update_time > timedelta(hours=12):
            self.fetch_phishing_urls()

phishing_data = PhishingData()
