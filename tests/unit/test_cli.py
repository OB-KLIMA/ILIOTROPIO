import logging

import pytest

from template_repo.cli import main


def test_main_logs_greeting(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.INFO)
    main()
    assert caplog.messages == ["Hello from template-repo!"]
