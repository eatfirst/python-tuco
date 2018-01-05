import os

import pytest


@pytest.fixture()
def dont_run_in_appveyor():
    if is_running_in_appveyor():
        pytest.skip('This test does not work on appveyor')

    return True


def is_running_in_appveyor():
    return os.environ.get('APPVEYOR', '').lower() == 'true'
