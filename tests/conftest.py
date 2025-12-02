"""
Test configuration for pytest
"""

import pytest
import logging


def pytest_configure(config):
    """Configure pytest"""
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests (require API credentials)"
    )


@pytest.fixture(autouse=True)
def setup_logging():
    """Setup logging for tests"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
