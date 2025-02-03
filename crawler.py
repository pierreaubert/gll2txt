"""Module for crawling and extracting speaker specifications from web content."""

import re
import logging
import asyncio
from dataclasses import dataclass
from typing import List, Optional, Dict, Tuple
import aiohttp
from bs4 import BeautifulSoup
import urllib.parse

@dataclass
class SpecData:
    """Speaker specification data"""
    frequency_response: Optional[Tuple[float, float]] = None  # Hz
    max_spl: Optional[float] = None  # dB
    width: Optional[float] = None  # mm
    height: Optional[float] = None  # mm
    depth: Optional[float] = None  # mm
    weight: Optional[float] = None  # kg
    amplifier_power: Optional[Dict[str, float]] = None  # Watts per driver
    sensitivity: Optional[float] = None  # dB/W/m
    impedance: Optional[float] = None  # Ohms
    source_url: Optional[str] = None  # URL where specifications were found

class ManufacturerCatalog:
    """Product catalog endpoints for different manufacturers"""
    
    NEUMANN_MONITORS = "https://neumann.com/en/products/monitors"
    GENELEC_MONITORS = "https://www.genelec.com/studio-monitors"
    JBL_MONITORS = "https://jblpro.com/en/studio-monitors"

class SpecificationCrawler:
    """Crawler for speaker specifications"""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        # Set debug level
        self.logger.setLevel(logging.DEBUG)
        # Add console handler if none exists
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            handler.setLevel(logging.DEBUG)
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
        
        # Add retry settings
        self.max_retries = 3
        self.retry_delay = 2  # seconds
    
    async def search_web(self, query: str) -> List[str]:
        """Search for speaker specifications using product catalogs"""
        query_lower = query.lower()
        urls = []
        
        # Extract brand and model
        brand = None
        model = None
        
        if "genelec" in query_lower:
            brand = "genelec"
            match = re.search(r'genelec\s*(\d+[a-z0-9\-]*)', query_lower)
            if match:
                model = match.group(1)
        elif "neumann" in query_lower:
            brand = "neumann"
            # Improved pattern for Neumann models, especially KH series with DSP
            match = re.search(r'neumann\s*kh\s*(\d+)(?:\s*(dsp|a))?', query_lower)
            if match:
                model = f"kh{match.group(1)}"
                if match.group(2):
                    model += f"-{match.group(2)}"
        elif "jbl" in query_lower:
            brand = "jbl"
            match = re.search(r'jbl\s*(\d+[a-z0-9\-]*)', query_lower)
            if match:
                model = match.group(1)
        
        self.logger.debug(f"Extracted brand: {brand}, model: {model}")
        
        if brand and model:
            model_clean = model.lower().replace(" ", "").replace("-", "")
            model_parts = re.findall(r'\d+|[a-z]+', model_clean)
            self.logger.debug(f"Model parts for matching: {model_parts}")
            
            for attempt in range(self.max_retries):
                try:
                    async with aiohttp.ClientSession() as session:
                        headers = {
                            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                            "Accept-Language": "en-US,en;q=0.9",
                        }
                        
                        # Get catalog URL based on brand
                        if brand == "neumann":
                            # Try both the catalog and direct product pages
                            catalog_urls = [
                                ManufacturerCatalog.NEUMANN_MONITORS,
                                f"https://neumann.com/en/products/monitors/{model.lower()}"
                            ]
                        elif brand == "genelec":
                            catalog_urls = [ManufacturerCatalog.GENELEC_MONITORS]
                        elif brand == "jbl":
                            catalog_urls = [ManufacturerCatalog.JBL_MONITORS]
                        
                        for catalog_url in catalog_urls:
                            self.logger.debug(f"Fetching catalog: {catalog_url}")
                            async with session.get(catalog_url, headers=headers, timeout=10) as response:
                                self.logger.debug(f"Catalog response status: {response.status}")
                                if response.status == 200:
                                    content = await response.text()
                                    self.logger.debug(f"Catalog content length: {len(content)}")
                                    soup = BeautifulSoup(content, 'html.parser')
                                    
                                    if brand == "neumann":
                                        # Check if we're already on a product page
                                        if "products/monitors/" in catalog_url and response.status == 200:
                                            # Verify the URL contains at least one part of the model name
                                            url_lower = catalog_url.lower()
                                            if any(part in url_lower for part in model_parts):
                                                urls.append(catalog_url)
                                                break
                                        
                                        # Otherwise search in catalog
                                        product_links = soup.find_all('a', href=True)
                                        self.logger.debug(f"Found {len(product_links)} links in catalog")
                                        for link in product_links:
                                            url = link['href'].lower()
                                            # Skip URLs that don't contain any part of the model name
                                            if not any(part in url for part in model_parts):
                                                continue
                                            
                                            self.logger.debug(f"Found matching link: {url}")
                                            if not url.startswith('http'):
                                                url = urllib.parse.urljoin("https://neumann.com", url)
                                            urls.append(url)
                                            break
                                    
                                    elif brand == "genelec":
                                        product_links = soup.find_all('a', href=True)
                                        self.logger.debug(f"Found {len(product_links)} links in catalog")
                                        for link in product_links:
                                            url = link['href'].lower()
                                            # Skip URLs that don't contain any part of the model name
                                            if not any(part in url for part in model_parts):
                                                continue
                                            
                                            self.logger.debug(f"Found matching link: {url}")
                                            if not url.startswith('http'):
                                                url = urllib.parse.urljoin("https://www.genelec.com", url)
                                            urls.append(url)
                                            break
                                    
                                    elif brand == "jbl":
                                        product_links = soup.find_all('a', href=True)
                                        self.logger.debug(f"Found {len(product_links)} links in catalog")
                                        for link in product_links:
                                            url = link['href'].lower()
                                            # Skip URLs that don't contain any part of the model name
                                            if not any(part in url for part in model_parts):
                                                continue
                                            
                                            self.logger.debug(f"Found matching link: {url}")
                                            if not url.startswith('http'):
                                                url = urllib.parse.urljoin("https://jblpro.com", url)
                                            urls.append(url)
                                            break
                        
                        if urls:
                            break
                    
                except Exception as e:
                    self.logger.error(f"Attempt {attempt + 1} failed: {str(e)}")
                    if attempt < self.max_retries - 1:
                        await asyncio.sleep(self.retry_delay)
                    else:
                        self.logger.error("All attempts failed")
        
        self.logger.debug(f"Found URLs: {urls}")
        return urls
    
    async def fetch_url_content(self, url: str) -> str:
        """Fetch and parse content from a URL"""
        for attempt in range(self.max_retries):
            try:
                async with aiohttp.ClientSession() as session:
                    headers = {
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                        "Accept-Language": "en-US,en;q=0.9",
                    }
                    
                    async with session.get(url, headers=headers, timeout=10) as response:
                        if response.status != 200:
                            self.logger.debug(f"Failed to fetch {url} (status {response.status})")
                            if attempt < self.max_retries - 1:
                                await asyncio.sleep(self.retry_delay)
                                continue
                            return ""
                        
                        content = await response.text()
                        self.logger.debug(f"Successfully retrieved content from {url}")
                        
                        # Parse based on the domain
                        soup = BeautifulSoup(content, 'html.parser')
                        specs = ""
                        
                        if "neumann.com" in url:
                            # Look for specifications in various sections
                            for selector in [
                                'div.technical-data',
                                'div.specifications',
                                'div.product-specifications',
                                'div.tech-specs',
                                'table.tech-specs',
                                'div[data-tab="specifications"]'
                            ]:
                                tech_data = soup.select_one(selector)
                                if tech_data:
                                    specs = tech_data.get_text(strip=True)
                                    break
                            
                            # If still no specs found, try to find any div containing "specifications" in its text
                            if not specs:
                                for div in soup.find_all('div'):
                                    if 'specification' in div.get_text().lower():
                                        specs = div.get_text(strip=True)
                                        break
                        
                        elif "genelec.com" in url:
                            # Look for specifications in the specifications section
                            spec_div = soup.find('div', class_='specifications')
                            if spec_div:
                                specs = spec_div.get_text(strip=True)
                            else:
                                # Try alternate class names
                                spec_div = soup.find('div', class_='technical-specifications')
                                if spec_div:
                                    specs = spec_div.get_text(strip=True)
                        
                        elif "jblpro.com" in url:
                            # Look for specifications in the tech specs section
                            spec_div = soup.find('div', class_='tech-specs')
                            if spec_div:
                                specs = spec_div.get_text(strip=True)
                            else:
                                # Try alternate class names
                                spec_div = soup.find('div', class_='specifications')
                                if spec_div:
                                    specs = spec_div.get_text(strip=True)
                        
                        return specs if specs else content
            
            except Exception as e:
                self.logger.error(f"Attempt {attempt + 1} failed for {url}: {str(e)}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay)
                else:
                    self.logger.error("All attempts failed")
                    return ""
    
    def extract_specifications(self, text: str, url: str) -> SpecData:
        """Extract specifications from text content"""
        specs = SpecData()
        specs.source_url = url  # Store the source URL
        
        try:
            # Convert text to lowercase for easier matching
            text_lower = text.lower()
            
            # Extract frequency response
            freq_matches = re.findall(r'frequency\s+response[^\d]*(\d+(?:\.\d+)?)\s*(?:hz|hertz)[^\d]*(\d+(?:\.\d+)?)\s*(?:hz|hertz|khz|k)', text_lower)
            if freq_matches:
                low, high = freq_matches[0]
                high = float(high)
                if 'k' in text_lower[text_lower.find(str(high)):text_lower.find(str(high))+10]:
                    high *= 1000
                specs.frequency_response = (float(low), high)
            
            # Extract max SPL
            spl_matches = re.findall(r'(?:maximum|max)?\s*spl[^\d]*(\d+(?:\.\d+)?)\s*(?:db|dba|dbu)', text_lower)
            if spl_matches:
                specs.max_spl = float(spl_matches[0])
            
            # Extract dimensions
            dim_matches = re.findall(r'dimensions[^\d]*(\d+(?:\.\d+)?)[^\d]*(?:x|\*)[^\d]*(\d+(?:\.\d+)?)[^\d]*(?:x|\*)[^\d]*(\d+(?:\.\d+)?)\s*(?:mm|cm|m)', text_lower)
            if dim_matches:
                w, h, d = dim_matches[0]
                unit = re.search(r'(\d+(?:\.\d+)?)\s*(mm|cm|m)', text_lower)
                if unit:
                    unit = unit.group(2)
                    specs.width = self.convert_to_metric(float(w), unit)
                    specs.height = self.convert_to_metric(float(h), unit)
                    specs.depth = self.convert_to_metric(float(d), unit)
            
            # Extract weight
            weight_matches = re.findall(r'weight[^\d]*(\d+(?:\.\d+)?)\s*(?:kg|g|lbs?)', text_lower)
            if weight_matches:
                weight = float(weight_matches[0])
                unit = re.search(r'(\d+(?:\.\d+)?)\s*(kg|g|lbs?)', text_lower)
                if unit:
                    unit = unit.group(2)
                    specs.weight = self.convert_to_metric_weight(weight, unit)
            
            # Extract amplifier power
            amp_matches = re.findall(r'(?:amplifier|amp)[^\d]*(\d+(?:\.\d+)?)\s*(?:w|watts?)', text_lower)
            if amp_matches:
                specs.amplifier_power = {"total": float(amp_matches[0])}
            
            # Try to extract per-driver power
            woofer_matches = re.findall(r'(?:woofer|lf)[^\d]*(\d+(?:\.\d+)?)\s*(?:w|watts?)', text_lower)
            tweeter_matches = re.findall(r'(?:tweeter|hf)[^\d]*(\d+(?:\.\d+)?)\s*(?:w|watts?)', text_lower)
            
            if woofer_matches or tweeter_matches:
                specs.amplifier_power = {}
                if woofer_matches:
                    specs.amplifier_power["woofer"] = float(woofer_matches[0])
                if tweeter_matches:
                    specs.amplifier_power["tweeter"] = float(tweeter_matches[0])
            
            # Extract sensitivity
            sens_matches = re.findall(r'sensitivity[^\d]*(\d+(?:\.\d+)?)\s*(?:db(?:/w(?:/m)?)?)', text_lower)
            if sens_matches:
                specs.sensitivity = float(sens_matches[0])
            # Alternative patterns for sensitivity
            if not specs.sensitivity:
                alt_sens_matches = re.findall(r'(\d+(?:\.\d+)?)\s*db(?:/w(?:/m)?)', text_lower)
                if alt_sens_matches:
                    specs.sensitivity = float(alt_sens_matches[0])
            
            # Extract impedance
            imp_matches = re.findall(r'(?:impedance|nominal\s+impedance)[^\d]*(\d+(?:\.\d+)?)\s*(?:ohms?|Ω)', text_lower)
            if imp_matches:
                specs.impedance = float(imp_matches[0])
            # Alternative pattern for impedance
            if not specs.impedance:
                alt_imp_matches = re.findall(r'(\d+(?:\.\d+)?)\s*(?:ohms?|Ω)', text_lower)
                if alt_imp_matches:
                    specs.impedance = float(alt_imp_matches[0])
        
        except Exception as e:
            self.logger.error(f"Error extracting specifications: {str(e)}")
        
        return specs
    
    def convert_to_metric(self, value: float, unit: str) -> float:
        """Convert length measurements to metric (mm)"""
        # Length conversions
        if unit in ["in", "inch", "inches"]:
            return value * 25.4  # Convert to mm
        elif unit == "cm":
            return value * 10  # Convert to mm
        elif unit == "m":
            return value * 1000  # Convert to mm
        return value  # Already in mm
    
    def convert_to_metric_weight(self, value: float, unit: str) -> float:
        """Convert weight measurements to metric (kg)"""
        if unit == "g":
            return value / 1000  # Convert to kg
        elif unit in ["lb", "lbs"]:
            return value * 0.45359237  # Convert to kg
        return value  # Already in kg
