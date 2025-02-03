"""Tests for the crawler module."""

import os
import pytest
from crawler import SpecificationCrawler, SpecData


# Test data directory
TEST_DATA_DIR = os.path.join(os.path.dirname(__file__), "test_data")


def load_mock_data(filename: str) -> str:
    """Load mock HTML data from file."""
    with open(os.path.join(TEST_DATA_DIR, filename), "r", encoding="utf-8") as f:
        return f.read()


@pytest.fixture
def crawler():
    """Create a SpecificationCrawler instance."""
    return SpecificationCrawler()


@pytest.fixture
def mock_search_results():
    """Load mock search results."""
    return {
        "Genelec 8341A": load_mock_data("genelec_8341a_search.html"),
        "Neumann KH 80A": load_mock_data("neumann_kh80a_search.html"),
        "JBL 130A": load_mock_data("jbl_130a_search.html"),
    }


@pytest.fixture
def mock_spec_pages():
    """Load mock specification pages."""
    return {
        "Genelec 8341A": load_mock_data("genelec_8341a_specs.html"),
        "Neumann KH 80A": load_mock_data("neumann_kh80a_specs.html"),
        "JBL 130A": load_mock_data("jbl_130a_specs.html"),
    }


def test_extract_urls_from_search(crawler, mock_search_results):
    """Test URL extraction from search results."""
    # Test Genelec 8341A
    urls = crawler._extract_urls_from_search(mock_search_results["Genelec 8341A"])
    assert len(urls) > 0
    assert any("genelec" in url.lower() for url in urls)

    # Test Neumann KH 80A
    urls = crawler._extract_urls_from_search(mock_search_results["Neumann KH 80A"])
    assert len(urls) > 0
    assert any("neumann" in url.lower() for url in urls)

    # Test JBL 130A
    urls = crawler._extract_urls_from_search(mock_search_results["JBL 130A"])
    assert len(urls) > 0
    assert any("jbl" in url.lower() for url in urls)


def test_extract_specifications(crawler, mock_spec_pages):
    """Test specification extraction from content."""
    # Test Genelec 8341A
    specs = crawler.extract_specifications(
        mock_spec_pages["Genelec 8341A"], "https://www.genelec.com/8341a"
    )
    assert isinstance(specs, SpecData)
    assert specs.sensitivity is not None
    assert 80 <= specs.sensitivity <= 100  # Typical range for studio monitors
    assert specs.impedance == 8  # Standard impedance
    assert specs.weight is not None
    assert all(x is not None for x in [specs.height, specs.width, specs.depth])

    # Test Neumann KH 80A
    specs = crawler.extract_specifications(
        mock_spec_pages["Neumann KH 80A"], "https://www.neumann.com/kh-80-dsp-a"
    )
    assert isinstance(specs, SpecData)
    assert specs.sensitivity is not None
    assert specs.impedance is not None
    assert specs.weight is not None
    assert all(x is not None for x in [specs.height, specs.width, specs.depth])

    # Test JBL 130A
    specs = crawler.extract_specifications(
        mock_spec_pages["JBL 130A"], "https://www.jblpro.com/130a"
    )
    assert isinstance(specs, SpecData)
    assert specs.sensitivity is not None
    assert specs.impedance is not None
    assert specs.weight is not None


def test_convert_to_metric(crawler):
    """Test unit conversion to metric."""
    # Weight conversions
    assert crawler.convert_to_metric(10, "lb") == pytest.approx(4.54, rel=1e-2)
    assert crawler.convert_to_metric(10, "lbs") == pytest.approx(4.54, rel=1e-2)
    assert crawler.convert_to_metric(10, "pound") == pytest.approx(4.54, rel=1e-2)

    # Length conversions
    assert crawler.convert_to_metric(10, "in") == pytest.approx(254.0)
    assert crawler.convert_to_metric(10, "inch") == pytest.approx(254.0)
    assert crawler.convert_to_metric(1, "ft") == pytest.approx(304.8)
    assert crawler.convert_to_metric(100, "cm") == pytest.approx(1000.0)
    assert crawler.convert_to_metric(1, "m") == pytest.approx(1000.0)

    # Already metric
    assert crawler.convert_to_metric(100, "mm") == 100
    assert crawler.convert_to_metric(10, "kg") == 10
