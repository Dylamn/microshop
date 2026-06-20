# ===========================================================================
# Unit conftest file
# ===========================================================================

from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture
from sqlalchemy.orm import Session


@pytest.fixture
def mock_db(mocker: MockerFixture) -> MagicMock:
    return mocker.MagicMock(spec=Session)
