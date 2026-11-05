import logging

import pytest

from iliotropio.cli import main


def test_main_logs_greeting(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.INFO)
    main()
    assert caplog.messages == ["Hello from iliotropio!"]
