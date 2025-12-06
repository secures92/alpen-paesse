import re
import requests
import traceback
from datetime import datetime
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from urllib.parse import urljoin
import logging

# Configure logging
logger = logging.getLogger(__name__)

try:
    from bs4 import BeautifulSoup
except ImportError:
    raise ImportError("beautifulsoup4 is required. Install with: pip install beautifulsoup4")


@dataclass
class AlpinePass:
    """
    Represents a Swiss Alpine Pass with current status and conditions.
    
    Attributes:
        name (str): Name of the pass
        route (str): Start and end locations (e.g., "Preda - La Punt Chamues-ch")
        status (str): Current pass status (e.g., "Open, no restrictions")
        temperature (Optional[float]): Current temperature in Celsius
        last_update (Optional[str]): Last update timestamp
        url (str): URL to detailed pass information
        elevation (Optional[int]): Pass elevation in meters
        notes (Optional[str]): Additional notes or restrictions
    """
    name: str
    route: str
    status: str
    temperature: Optional[float] = None
    last_update: Optional[str] = None
    url: str = ""
    elevation: Optional[int] = None
    notes: Optional[str] = None
    
    def __str__(self) -> str:
        """String representation of the alpine pass."""
        temp_str = f"{self.temperature}°C" if self.temperature is not None else "N/A"
        return f"{self.name} ({self.route}): {self.status} - {temp_str}"
    
    def is_open(self) -> bool:
        """Check if the pass is currently open."""
        if not self.status:
            return False
        status_lower = self.status.lower()
        return any(keyword in status_lower for keyword in ['open', 'offen', 'befahrbar'])
    
    def has_restrictions(self) -> bool:
        """Check if the pass has any restrictions."""
        if not self.status:
            return False
        status_lower = self.status.lower()
        return any(keyword in status_lower for keyword in [
            'restriction', 'chain', 'winter', 'snow', 'closed',
            'einschränkung', 'ketten', 'winter', 'schnee', 'gesperrt'
        ])


class AlpenPasseScraper:
    """
    Scraper for alpen-paesse.ch website to fetch Swiss Alpine Pass information.
    """
    
    BASE_URL = "https://alpen-paesse.ch"
    MAIN_PAGE_DE = f"{BASE_URL}/de/"
    MAIN_PAGE_EN = f"{BASE_URL}/en/"
    
    def __init__(self, language: str = "en", timeout: int = 10):
        """
        Initialize the scraper.
        
        Args:
            language (str): Language for scraping ("en" or "de")
            timeout (int): Request timeout in seconds
        """
        self.language = language.lower()
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
        if self.language not in ["en", "de"]:
            raise ValueError("Language must be 'en' or 'de'")
            
        self.main_url = self.MAIN_PAGE_EN if language == "en" else self.MAIN_PAGE_DE
    
    def _make_request(self, url: str) -> Optional[requests.Response]:
        """
        Make a HTTP request with error handling.
        
        Args:
            url (str): URL to request
            
        Returns:
            Optional[requests.Response]: Response object or None if failed
        """
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed for {url}: {e}")
            return None
    
    def _extract_temperature(self, text: str) -> Optional[float]:
        """
        Extract temperature from text using regex.
        
        Args:
            text (str): Text containing temperature information
            
        Returns:
            Optional[float]: Temperature in Celsius or None if not found
        """
        if not text:
            return None
            
        # Pattern matches temperatures like "-5°C", "12°C", "5.5°C"
        temp_pattern = r'(-?\d+(?:\.\d+)?)°C'
        match = re.search(temp_pattern, text)
        
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                pass
        
        # Alternative pattern for temperatures without °C
        temp_pattern2 = r'(-?\d+(?:\.\d+)?)\s*°?C?'
        match = re.search(temp_pattern2, text)
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                pass
                
        return None
    
    def _extract_update_time(self, text: str) -> Optional[str]:
        """
        Extract last update time from text.
        
        Args:
            text (str): Text containing update information
            
        Returns:
            Optional[str]: Update timestamp or None if not found
        """
        if not text:
            return None
            
        # Pattern for dates like "07.07.2025, 07:16" or "Updated on: 07.07.2025, 07:16"
        date_patterns = [
            r'(\d{1,2}\.\d{1,2}\.\d{4},?\s+\d{1,2}:\d{2})',
            r'Updated on:\s*(\d{1,2}\.\d{1,2}\.\d{4},?\s+\d{1,2}:\d{2})',
            r'Aktualisiert am:\s*(\d{1,2}\.\d{1,2}\.\d{4},?\s+\d{1,2}:\d{2})'
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1).strip()
                
        return None
    
    def _parse_pass_section(self, section) -> Optional[AlpinePass]:
        """
        Parse a pass section from the HTML to extract pass information.
        
        Args:
            section: BeautifulSoup element containing pass information
            
        Returns:
            Optional[AlpinePass]: Parsed pass object or None if parsing failed
        """
        try:
            # Extract pass name and URL - try multiple strategies
            name_link = None
            name = ""
            
            # Strategy 1: Look for links with common class names
            name_link = section.find('a', class_=lambda x: x and any(
                keyword in str(x).lower() for keyword in ['title', 'name', 'heading', 'pass']
            ))
            
            # Strategy 2: Fall back to first link
            if not name_link:
                name_link = section.find('a')
            
            # Strategy 3: Look for heading tags
            if not name_link:
                heading = section.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
                if heading:
                    name_link = heading.find('a')
                    if not name_link:
                        name = heading.get_text(strip=True)
                        # Try to find a link in the same section
                        name_link = section.find('a', href=True)
            
            if not name_link and not name:
                logger.debug(f"No name link found in section: {section.get_text()[:100]}")
                return None
            
            if name_link:
                name = name_link.get_text(strip=True)
                href = name_link.get('href', '')
                if href:
                    pass_url = urljoin(self.BASE_URL, href)
                else:
                    pass_url = ""
            else:
                pass_url = ""
            
            # Skip if name is empty or too short
            if not name or len(name) < 3:
                return None
            
            # Extract route information - try multiple strategies
            route_text = ""
            
            # Strategy 1: Look for elements with route/description classes
            route_elem = section.find(class_=lambda x: x and any(
                keyword in str(x).lower() for keyword in ['route', 'description', 'subtitle', 'strecke']
            ))
            if route_elem:
                route_text = route_elem.get_text(strip=True)
            
            # Strategy 2: Fall back to text with dash pattern
            if not route_text:
                route_elements = section.find_all(string=True)
                for text in route_elements:
                    text_clean = text.strip()
                    if ' - ' in text_clean and len(text_clean) < 100 and text_clean != name:
                        route_text = text_clean
                        break
            
            # Extract status - try multiple strategies
            status = "Unknown"
            
            # Strategy 1: Look for elements with status classes
            status_elem = section.find(class_=lambda x: x and any(
                keyword in str(x).lower() for keyword in ['status', 'state', 'zustand', 'condition']
            ))
            if status_elem:
                status = status_elem.get_text(strip=True)
            
            # Strategy 2: Fall back to text search
            if status == "Unknown":
                status_elements = section.find_all(text=True)
                for text in status_elements:
                    text_clean = text.strip()
                    text_lower = text_clean.lower()
                    if any(keyword in text_lower for keyword in [
                        'open', 'offen', 'closed', 'gesperrt', 'befahrbar', 'restriction',
                        'geöffnet', 'geschlossen', 'passierbar', 'einschränkung'
                    ]) and len(text_clean) > 3 and len(text_clean) < 150:
                        status = text_clean
                        break
            
            # Extract temperature - try multiple strategies
            temperature = None
            
            # Strategy 1: Look for elements with temperature classes
            temp_elem = section.find(class_=lambda x: x and any(
                keyword in str(x).lower() for keyword in ['temp', 'temperature', 'weather']
            ))
            if temp_elem:
                temperature = self._extract_temperature(temp_elem.get_text())
            
            # Strategy 2: Fall back to text search
            if temperature is None:
                temp_elements = section.find_all(text=True)
                for text in temp_elements:
                    temp = self._extract_temperature(text)
                    if temp is not None:
                        temperature = temp
                        break
            
            # Extract last update - try multiple strategies
            last_update = None
            
            # Strategy 1: Look for elements with update/time classes
            update_elem = section.find(class_=lambda x: x and any(
                keyword in str(x).lower() for keyword in ['update', 'date', 'time', 'aktualisiert', 'datum']
            ))
            if update_elem:
                last_update = self._extract_update_time(update_elem.get_text())
            
            # Strategy 2: Look for time tags
            if not last_update:
                time_elem = section.find('time')
                if time_elem:
                    last_update = self._extract_update_time(time_elem.get_text())
                    # Also check datetime attribute
                    if not last_update and time_elem.get('datetime'):
                        last_update = time_elem.get('datetime')
            
            # Strategy 3: Fall back to text search
            if not last_update:
                update_elements = section.find_all(text=True)
                for text in update_elements:
                    update = self._extract_update_time(text)
                    if update:
                        last_update = update
                        break
            
            # Extract notes (winter restrictions, etc.)
            notes = ""
            note_texts = section.find_all(text=True)
            for text in note_texts:
                text_clean = text.strip()
                if any(keyword in text_clean.lower() for keyword in [
                    'winter', 'snow', 'chain', 'restriction', 'obligatory',
                    'schnee', 'ketten', 'einschränkung', 'obligatorisch'
                ]) and len(text_clean) > 20 and text_clean != status:
                    notes = text_clean[:200] + "..." if len(text_clean) > 200 else text_clean
                    break
            
            logger.debug(f"Parsed pass: {name}, Status: {status}, Temp: {temperature}, Update: {last_update}")
            
            return AlpinePass(
                name=name,
                route=route_text,
                status=status,
                temperature=temperature,
                last_update=last_update,
                url=pass_url,
                notes=notes if notes else None
            )
            
        except Exception as e:
            logger.error(f"Error parsing pass section: {e}")
            logger.debug(f"Traceback: {traceback.format_exc()}")
            return None
    
    def get_all_passes(self) -> List[AlpinePass]:
        """
        Fetch information for all Alpine passes from the main page.
        
        Returns:
            List[AlpinePass]: List of all available Alpine passes
        """
        response = self._make_request(self.main_url)
        if not response:
            logger.error("Failed to fetch main page")
            return []
        
        try:
            soup = BeautifulSoup(response.content, 'html.parser')
            passes = []
            
            # Try multiple strategies to find pass information
            # Strategy 1: Look for pass cards with specific CSS classes (new website structure)
            pass_cards = soup.find_all(['div', 'article', 'section'], class_=lambda x: x and any(
                keyword in str(x).lower() for keyword in ['pass', 'paesse', 'card', 'item', 'entry']
            ))
            
            if pass_cards:
                logger.debug(f"Found {len(pass_cards)} potential pass cards using CSS classes")
                processed_names = set()
                for card in pass_cards:
                    pass_info = self._parse_pass_section(card)
                    if pass_info and pass_info.name and pass_info.name not in processed_names:
                        passes.append(pass_info)
                        processed_names.add(pass_info.name)
            
            # Strategy 2: If no cards found, try the old method with updated URL patterns
            if not passes:
                logger.debug("No passes found with CSS classes, trying link-based approach")
                pass_links = soup.find_all('a', href=True)
                
                processed_names = set()  # Avoid duplicates
                
                # Support multiple URL patterns
                url_patterns = ['/alpenpaesse/', '/passes/', '/de/alpenpass/', '/paesse/']
                
                for link in pass_links:
                    href = link.get('href', '')
                    # Check if link matches any known pattern
                    if href and any(pattern in href for pattern in url_patterns) and href not in processed_names:
                        # Find the parent section containing this pass
                        section = link.find_parent()
                        max_depth = 5  # Limit parent traversal
                        depth = 0
                        while section and hasattr(section, 'name') and section.name != 'body' and depth < max_depth:
                            # Look for temperature and status information in this section
                            section_text = section.get_text()
                            if '°C' in section_text and any(keyword in section_text.lower() 
                                                           for keyword in ['open', 'offen', 'updated', 'aktualisiert', 'status', 'zustand']):
                                pass_info = self._parse_pass_section(section)
                                if pass_info and pass_info.name not in processed_names:
                                    passes.append(pass_info)
                                    processed_names.add(pass_info.name)
                                    break
                            section = section.find_parent()
                            depth += 1
            
            logger.info(f"Successfully parsed {len(passes)} passes")
            if not passes:
                logger.warning("No passes found - website structure may have changed")
                logger.debug(f"Page content preview: {soup.get_text()[:500]}")
            return passes
            
        except Exception as e:
            logger.error(f"Error parsing main page: {e}")
            logger.debug(f"Traceback: {traceback.format_exc()}")
            return []
    
    def get_pass_details(self, pass_name: str) -> Optional[AlpinePass]:
        """
        Get detailed information for a specific pass.
        
        Args:
            pass_name (str): Name of the pass
            
        Returns:
            Optional[AlpinePass]: Detailed pass information or None if not found
        """
        passes = self.get_all_passes()
        for pass_info in passes:
            if pass_name.lower() in pass_info.name.lower():
                return pass_info
        return None
    
    def get_open_passes(self) -> List[AlpinePass]:
        """
        Get list of currently open passes.
        
        Returns:
            List[AlpinePass]: List of open passes
        """
        all_passes = self.get_all_passes()
        return [p for p in all_passes if p.is_open()]
    
    def get_passes_with_restrictions(self) -> List[AlpinePass]:
        """
        Get list of passes with current restrictions.
        
        Returns:
            List[AlpinePass]: List of passes with restrictions
        """
        all_passes = self.get_all_passes()
        return [p for p in all_passes if p.has_restrictions()]


def get_all_mountain_passes(language: str = "en") -> List[AlpinePass]:
    """
    Convenience function to get all mountain passes.
    
    Args:
        language (str): Language for data retrieval ("en" or "de")
        
    Returns:
        List[AlpinePass]: List of all Alpine passes
    """
    scraper = AlpenPasseScraper(language=language)
    return scraper.get_all_passes()


def find_pass(name: str, language: str = "en") -> Optional[AlpinePass]:
    """
    Find a specific pass by name.
    
    Args:
        name (str): Pass name to search for
        language (str): Language for data retrieval ("en" or "de")
        
    Returns:
        Optional[AlpinePass]: Found pass or None
    """
    scraper = AlpenPasseScraper(language=language)
    return scraper.get_pass_details(name)
