import asyncio

import pytest

from app.store import ping_db


def pytest_configure(config):
    config.addinivalue_line("markers", "mongo: requires a running MongoDB instance")


def pytest_collection_modifyitems(config, items):
    if asyncio.run(ping_db()):
        return

    skip = pytest.mark.skip(reason="MongoDB is not available at the configured URI")
    for item in items:
        if "mongo" in item.keywords:
            item.add_marker(skip)
