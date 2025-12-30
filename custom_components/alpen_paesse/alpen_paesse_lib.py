import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Any


class AlpenPaesseFetcher:
    """
    A Python library to fetch data about alpine passes from alpen-paesse.ch.
    """
    BASE_URL = "https://alpen-paesse.ch"

    def __init__(self, language_path: str = "/de"):
        """
        Initializes the fetcher with the base URL and a language path.
        The full URL will be: BASE_URL + language_path + '/#'.
        """
        self.url = f"{self.BASE_URL}{language_path}/#"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

    def fetch_html(self) -> str:
        """
        Fetches the HTML content of the main passes page.
        """
        print(f"Fetching data from: {self.url}")
        try:
            response = requests.get(self.url, headers=self.headers, timeout=10)
            response.raise_for_status()  # Raise an HTTPError for bad responses (4xx or 5xx)
            return response.text
        except requests.exceptions.RequestException as e:
            print(f"Error fetching page: {e}")
            return ""

    def parse_pass_element(self, element: BeautifulSoup) -> Dict[str, Any]:
        """
        Parses a single 'passes-element-item' (Alpenpass) and extracts all data.
        """
        data = {}

        # 1. Pass Name and Detail Link
        title_link = element.select_one('.pass-card-title a.pass-card-link')
        if title_link:
            data['name'] = title_link.text.strip()
            data['detail_url'] = self.BASE_URL + title_link.get('href', '')
        else:
            return None  # Skip if no pass name is found

        # 2. Status and Last Update
        status_badge = element.select_one(
            '.pass-card-row:nth-child(1) > .pass-card-badge:nth-child(1) .pass-card-badge-text')
        if status_badge:
            data['current_status_description'] = status_badge.select_one(
                'div:nth-child(1)').text.strip() if status_badge.select_one('div:nth-child(1)') else ''

            last_update_el = status_badge.select_one(
                '.pass-card-badge-text-clamp-1')
            if last_update_el:
                # Clean up the prefix "Unverändert gültig seit::"
                data['status_last_update'] = last_update_el.text.replace(
                    'Unverändert gültig seit::', '').strip()
            else:
                data['status_last_update'] = ''

        # 3. Weather/Temperature
        temp_el = element.select_one(
            '.pass-card-row:nth-child(1) > .pass-card-badge:nth-child(2) .pass-card-badge-text')
        data['temperature'] = temp_el.text.strip() if temp_el else ''


        return data

    def fetch_passes_data(self) -> List[Dict[str, Any]]:
        """
        Main method to fetch and parse data for all passes.
        """
        html_content = self.fetch_html()
        if not html_content:
            return []

        soup = BeautifulSoup(html_content, 'html.parser')

        # Target the main container and then iterate over all pass items
        passes_container = soup.find('section', class_='passes-element')
        if not passes_container:
            print("Could not find the main passes container on the page.")
            return []

        pass_elements = passes_container.find_all(
            'li', class_='passes-element-item')

        if not pass_elements:
            print("No pass elements found. The website structure may have changed.")
            return []

        passes_data = []
        for element in pass_elements:
            pass_data = self.parse_pass_element(element)
            if pass_data:
                passes_data.append(pass_data)

        return passes_data


# --- Example Usage ---
if __name__ == '__main__':
    # Initialize the fetcher for the German language path
    fetcher = AlpenPaesseFetcher(language_path="/de")

    # Fetch the data
    data = fetcher.fetch_passes_data()

    # Print the results
    if data:
        print(f"\nSuccessfully fetched data for {len(data)} alpine passes.")
        print("-" * 50)
        # Print the first few passes for a snapshot
        for i, pass_info in enumerate(data[:3]):
            print(f"Pass {i+1}: {pass_info['name']}")
            print(f"  Status: {pass_info['current_status_description']}")
            print(f"  Update: {pass_info['status_last_update']}")
            print(f"  Temp:   {pass_info['temperature']}")
            print(f"  Link:   {pass_info['detail_url']}")
            print("-" * 50)
    else:
        print("\nFailed to retrieve pass data.")