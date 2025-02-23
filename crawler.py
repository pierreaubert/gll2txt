"""Module for crawling and extracting speaker specifications from web content."""

import asyncio
import logging
import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import aiohttp
from bs4 import BeautifulSoup


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
    JBL_MONITORS = [
        "https://jblpro.com/en/products/m2-master-reference-monitor",  # Direct link for M2
        "https://jblpro.com/en/search?query=M2+master+reference+monitor",  # Search for M2
        "https://jblpro.com/en/products/recording-broadcast/studio-monitors",
        "https://jblpro.com/en/products/recording-broadcast/studio-reference-monitors",
        "https://www.jblpro.com/en/products/studio-monitors",
    ]


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
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
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
            match = re.search(r"genelec\s*(\d+[a-z0-9\-]*)", query_lower)
            if match:
                model = match.group(1)
        elif "neumann" in query_lower:
            brand = "neumann"
            # Improved pattern for Neumann models, especially KH series with DSP
            match = re.search(r"neumann\s*kh\s*(\d+)(?:\s*(dsp|a))?", query_lower)
            if match:
                model = f"kh{match.group(1)}"
                if match.group(2):
                    model += f"-{match.group(2)}"
        elif "jbl" in query_lower:
            brand = "jbl"
            # Updated pattern to handle models starting with letters (like M2) or numbers
            match = re.search(r"jbl\s*([a-z0-9]+(?:[a-z0-9\-]*[a-z0-9])?)", query_lower)
            if match:
                model = match.group(1)

        self.logger.debug(f"Extracted brand: {brand}, model: {model}")

        if brand and model:
            model_clean = model.lower().replace(" ", "").replace("-", "")
            model_parts = re.findall(r"\d+|[a-z]+", model_clean)
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
                                f"https://neumann.com/en/products/monitors/{model.lower()}",
                            ]
                        elif brand == "genelec":
                            catalog_urls = [ManufacturerCatalog.GENELEC_MONITORS]
                        elif brand == "jbl":
                            catalog_urls = ManufacturerCatalog.JBL_MONITORS
                            # Add model-specific URL if it's the M2
                            if model.lower() == "m2":
                                catalog_urls.append(
                                    "https://www.jblpro.com/en/products/m2-master-reference-monitor"
                                )

                        for catalog_url in catalog_urls:
                            self.logger.debug(f"Fetching catalog: {catalog_url}")
                            async with session.get(
                                catalog_url, headers=headers, timeout=10
                            ) as response:
                                self.logger.debug(
                                    f"Catalog response status: {response.status}"
                                )
                                if response.status == 200:
                                    content = await response.text()
                                    self.logger.debug(
                                        f"Catalog content length: {len(content)}"
                                    )
                                    urls = self._extract_urls_from_search(content)
                                    if urls:
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

    def _extract_urls_from_search(self, content: str) -> List[str]:
        """Extract product URLs from search results content."""
        urls = []
        try:
            soup = BeautifulSoup(content, "html.parser")
            # Find all links
            for link in soup.find_all("a", href=True):
                url = link["href"]
                # Skip non-product links
                if any(
                    skip in url.lower()
                    for skip in [
                        "#",
                        "javascript:",
                        "mailto:",
                        "/fr/",
                        "/zh/",
                        "/en-asia/",
                    ]
                ):
                    continue

                # Make sure URL is absolute
                if not url.startswith("http"):
                    if url.startswith("/"):
                        # Handle different domains
                        if "genelec" in url:
                            url = f"https://www.genelec.com{url}"
                        elif "neumann" in url:
                            url = f"https://www.neumann.com{url}"
                        elif "jblpro" in url:
                            url = f"https://jblpro.com{url}"
                    else:
                        continue

                # Only include product URLs from known manufacturers and retailers
                if not any(
                    domain in url.lower()
                    for domain in [
                        "genelec.com",
                        "neumann.com",
                        "jblpro.com",
                        "thomann.de",
                        "sweetwater.com",
                    ]
                ):
                    continue

                # Only include product pages
                if not any(
                    term in url.lower()
                    for term in [
                        "/products/",
                        "/store/detail/",
                        "/gb/",
                        "/8341",  # Genelec specific
                        "/kh",  # Neumann specific
                        "/m2",  # JBL specific
                    ]
                ):
                    continue

                # Skip duplicate URLs
                if url not in urls:
                    urls.append(url)

        except Exception as e:
            self.logger.error(f"Error extracting URLs from search: {str(e)}")
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

                    async with session.get(
                        url, headers=headers, timeout=10
                    ) as response:
                        if response.status != 200:
                            self.logger.debug(
                                f"Failed to fetch {url} (status {response.status})"
                            )
                            if attempt < self.max_retries - 1:
                                await asyncio.sleep(self.retry_delay)
                                continue
                            return ""

                        content = await response.text()
                        self.logger.debug(f"Successfully retrieved content from {url}")

                        # Parse based on the domain
                        soup = BeautifulSoup(content, "html.parser")
                        specs = ""

                        if "neumann.com" in url:
                            # Look for specifications in various sections
                            for selector in [
                                "div.technical-data",
                                "div.specifications",
                                "div.product-specifications",
                                "div.tech-specs",
                                "table.tech-specs",
                                'div[data-tab="specifications"]',
                            ]:
                                tech_data = soup.select_one(selector)
                                if tech_data:
                                    specs = tech_data.get_text(strip=True)
                                    break

                            # If still no specs found, try to find any div containing "specifications" in its text
                            if not specs:
                                for div in soup.find_all("div"):
                                    if "specification" in div.get_text().lower():
                                        specs = div.get_text(strip=True)
                                        break

                        elif "genelec.com" in url:
                            # Look for specifications in the specifications section
                            spec_div = soup.find("div", class_="specifications")
                            if spec_div:
                                specs = spec_div.get_text(strip=True)
                            else:
                                # Try alternate class names
                                spec_div = soup.find(
                                    "div", class_="technical-specifications"
                                )
                                if spec_div:
                                    specs = spec_div.get_text(strip=True)

                        elif "jblpro.com" in url:
                            # Look for specifications in the tech specs section
                            spec_div = soup.find("div", class_="tech-specs")
                            if spec_div:
                                specs = spec_div.get_text(strip=True)
                            else:
                                # Try alternate class names
                                spec_div = soup.find("div", class_="specifications")
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
        """Extract specifications from text"""
        try:
            soup = BeautifulSoup(text, "html.parser")
            specs = SpecData()
            specs.source_url = url

            # Try to find specifications in a table or list first
            spec_table = None
            for table in soup.find_all(["table", "div", "ul"]):
                if any(
                    keyword in str(table).lower()
                    for keyword in [
                        "specification",
                        "technical data",
                        "tech specs",
                        "product info",
                        "spec-list",
                        "product-specs",
                    ]
                ):
                    spec_table = table
                    break

            if spec_table:
                table_text = spec_table.get_text()
            else:
                table_text = text

            # Extract values from spec items
            for spec_item in soup.find_all("div", class_="spec-item"):
                label = spec_item.find("span", class_="label")
                value = spec_item.find("span", class_="value")
                if label and value:
                    label_text = label.get_text().strip().lower()
                    value_text = value.get_text().strip()

                    if "sensitivity" in label_text:
                        try:
                            specs.sensitivity = float(
                                re.search(r"(\d+(?:\.\d+)?)", value_text).group(1)
                            )
                        except (ValueError, AttributeError):
                            pass
                    elif "impedance" in label_text:
                        try:
                            specs.impedance = float(
                                re.search(r"(\d+(?:\.\d+)?)", value_text).group(1)
                            )
                        except (ValueError, AttributeError):
                            pass
                    elif "weight" in label_text:
                        try:
                            value = float(
                                re.search(r"(\d+(?:\.\d+)?)", value_text).group(1)
                            )
                            unit = re.search(
                                r"(kg|g|lb|lbs|pound|pounds)", value_text, re.IGNORECASE
                            ).group(1)
                            specs.weight = self.convert_to_metric_weight(value, unit)
                        except (ValueError, AttributeError):
                            pass
                    elif "height" in label_text:
                        try:
                            value = float(
                                re.search(r"(\d+(?:\.\d+)?)", value_text).group(1)
                            )
                            unit = re.search(
                                r"(mm|cm|m|in|inch|inches|ft|feet)",
                                value_text,
                                re.IGNORECASE,
                            ).group(1)
                            specs.height = self.convert_to_metric(value, unit)
                        except (ValueError, AttributeError):
                            pass
                    elif "width" in label_text:
                        try:
                            value = float(
                                re.search(r"(\d+(?:\.\d+)?)", value_text).group(1)
                            )
                            unit = re.search(
                                r"(mm|cm|m|in|inch|inches|ft|feet)",
                                value_text,
                                re.IGNORECASE,
                            ).group(1)
                            specs.width = self.convert_to_metric(value, unit)
                        except (ValueError, AttributeError):
                            pass
                    elif "depth" in label_text:
                        try:
                            value = float(
                                re.search(r"(\d+(?:\.\d+)?)", value_text).group(1)
                            )
                            unit = re.search(
                                r"(mm|cm|m|in|inch|inches|ft|feet)",
                                value_text,
                                re.IGNORECASE,
                            ).group(1)
                            specs.depth = self.convert_to_metric(value, unit)
                        except (ValueError, AttributeError):
                            pass

            # If no values found in spec items, try generic patterns
            if not any(
                [
                    specs.sensitivity,
                    specs.impedance,
                    specs.weight,
                    specs.height,
                    specs.width,
                    specs.depth,
                ]
            ):
                # Extract sensitivity
                sensitivity_pattern = (
                    r"(?:sensitivity|output level|spl).*?(\d+(?:\.\d+)?)\s*(?:db|dB)"
                )
                sensitivity_match = re.search(
                    sensitivity_pattern, table_text, re.IGNORECASE
                )
                if sensitivity_match:
                    try:
                        specs.sensitivity = float(sensitivity_match.group(1))
                    except ValueError:
                        pass

                # Extract impedance
                impedance_pattern = r"(?:impedance|nominal\s+impedance).*?(\d+(?:\.\d+)?)\s*(?:ohm|Ω|Ohm)"
                impedance_match = re.search(
                    impedance_pattern, table_text, re.IGNORECASE
                )
                if impedance_match:
                    try:
                        specs.impedance = float(impedance_match.group(1))
                    except ValueError:
                        pass

                # Try to find dimensions with labels first
                height_pattern = (
                    r"(?:height|h).*?(\d+(?:\.\d+)?)\s*(mm|cm|m|in|inch|inches|ft|feet)"
                )
                width_pattern = (
                    r"(?:width|w).*?(\d+(?:\.\d+)?)\s*(mm|cm|m|in|inch|inches|ft|feet)"
                )
                depth_pattern = (
                    r"(?:depth|d).*?(\d+(?:\.\d+)?)\s*(mm|cm|m|in|inch|inches|ft|feet)"
                )

                # Extract dimensions with labels
                height_match = re.search(height_pattern, table_text, re.IGNORECASE)
                width_match = re.search(width_pattern, table_text, re.IGNORECASE)
                depth_match = re.search(depth_pattern, table_text, re.IGNORECASE)

                if height_match:
                    try:
                        value = float(height_match.group(1))
                        unit = height_match.group(2)
                        specs.height = self.convert_to_metric(value, unit)
                    except ValueError:
                        pass

                if width_match:
                    try:
                        value = float(width_match.group(1))
                        unit = width_match.group(2)
                        specs.width = self.convert_to_metric(value, unit)
                    except ValueError:
                        pass

                if depth_match:
                    try:
                        value = float(depth_match.group(1))
                        unit = depth_match.group(2)
                        specs.depth = self.convert_to_metric(value, unit)
                    except ValueError:
                        pass

                # Extract weight
                weight_pattern = r"(?:weight|net\s+weight).*?(\d+(?:\.\d+)?)\s*(kg|g|lb|lbs|pound|pounds)"
                weight_match = re.search(weight_pattern, table_text, re.IGNORECASE)
                if weight_match:
                    try:
                        value = float(weight_match.group(1))
                        unit = weight_match.group(2)
                        specs.weight = self.convert_to_metric_weight(value, unit)
                    except ValueError:
                        pass

            return specs
        except Exception as e:
            self.logger.error(f"Error extracting specifications: {str(e)}")
            return SpecData(source_url=url)

    def convert_to_metric(self, value: float, unit: str) -> float:
        """Convert length measurements to metric (mm)"""
        unit = unit.lower()
        # Length conversions
        if unit in ["in", "inch", "inches"]:
            return value * 25.4  # Convert to mm
        elif unit in ["ft", "feet", "foot"]:
            return value * 304.8  # Convert to mm (12 inches * 25.4)
        elif unit == "cm":
            return value * 10  # Convert to mm
        elif unit == "m":
            return value * 1000  # Convert to mm
        elif unit in ["lb", "lbs", "pound", "pounds"]:
            return value * 0.45359237  # Convert to kg
        elif unit == "g":
            return value / 1000  # Convert to kg
        return value  # Already in mm or kg

    def convert_to_metric_weight(self, value: float, unit: str) -> float:
        """Convert weight measurements to metric (kg)"""
        unit = unit.lower()
        if unit == "g":
            return value / 1000  # Convert to kg
        elif unit in ["lb", "lbs", "pound", "pounds"]:
            return value * 0.45359237  # Convert to kg
        return value  # Already in kg
