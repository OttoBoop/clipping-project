"""Pytest configuration for the clipping project."""


def pytest_configure(config):
    config.addinivalue_line("markers", "live: marks tests as requiring network access (deselect with '-m \"not live\"')")
