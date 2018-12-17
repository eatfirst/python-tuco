"""Test configuration."""
import os

import pytest


@pytest.fixture()
def dont_run_in_appveyor():
    """Test if the app is not on AppVeyor."""
    if is_running_in_appveyor():
        pytest.skip("This test does not work on appveyor")

    return True


def is_running_in_appveyor():
    """Check if the AppVeyor environment variable is set."""
    return os.environ.get("APPVEYOR", "").lower() == "true"
