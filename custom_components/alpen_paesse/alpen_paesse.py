#!/usr/bin/env python3
"""
Swiss Alpine Pass Information Library

A simple Python library for scraping and representing Swiss alpine pass data
from alpen-paesse.ch. This library provides a clean API to fetch current
status, temperature, and other information about Swiss mountain passes.

Author: Generated for alpen-paesse.ch integration
Date: July 2025
"""

import re
import requests
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
            # Extract pass name and URL
            name_link = section.find('a')
            if not name_link:
                return None
                
            name = name_link.get_text(strip=True)
            href = name_link.get('href', '')
            if href:
                pass_url = urljoin(self.BASE_URL, href)
            else:
                pass_url = ""
            
            # Extract route information
            route_text = ""
            route_elements = section.find_all(string=True)
            for text in route_elements:
                text_clean = text.strip()
                if ' - ' in text_clean and len(text_clean) < 100:
                    route_text = text_clean
                    break
            
            # Extract status
            status = "Unknown"
            status_elements = section.find_all(text=True)
            for text in status_elements:
                text_clean = text.strip().lower()
                if any(keyword in text_clean for keyword in [
                    'open', 'offen', 'closed', 'gesperrt', 'befahrbar', 'restriction'
                ]):
                    status = text.strip()
                    break
            
            # Extract temperature
            temperature = None
            temp_elements = section.find_all(text=True)
            for text in temp_elements:
                temp = self._extract_temperature(text)
                if temp is not None:
                    temperature = temp
                    break
            
            # Extract last update
            last_update = None
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
                    'winter', 'schnee', 'ketten', 'einschränkung', 'obligatorisch'
                ]) and len(text_clean) > 20:
                    notes = text_clean[:200] + "..." if len(text_clean) > 200 else text_clean
                    break
            
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
            
            # Look for pass information sections
            # The passes seem to be in sections with links to individual pass pages
            pass_links = soup.find_all('a', href=True)
            
            processed_names = set()  # Avoid duplicates
            
            for link in pass_links:
                href = link.get('href', '')
                if href and '/alpenpaesse/' in href and href not in processed_names:
                    # Find the parent section containing this pass
                    section = link.find_parent()
                    while section and hasattr(section, 'name') and section.name != 'body':
                        # Look for temperature and status information in this section
                        section_text = section.get_text()
                        if '°C' in section_text and any(keyword in section_text.lower() 
                                                       for keyword in ['open', 'offen', 'updated', 'aktualisiert']):
                            pass_info = self._parse_pass_section(section)
                            if pass_info and pass_info.name not in processed_names:
                                passes.append(pass_info)
                                processed_names.add(pass_info.name)
                                break
                        section = section.find_parent()
            
            logger.info(f"Successfully parsed {len(passes)} passes")
            return passes
            
        except Exception as e:
            logger.error(f"Error parsing main page: {e}")
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