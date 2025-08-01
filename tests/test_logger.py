import logging

import pytest

from armctl import Logger
from armctl.templates import logger as logger_module


def test_send_level_name():
    assert logging.getLevelName(logger_module.SEND_LEVEL) == "SEND"


def test_receive_level_name():
    assert logging.getLevelName(logger_module.RECEIVE_LEVEL) == "RECV"


def test_logger_send_and_receive_methods_exist():
    log = logging.getLogger("test_logger")
    assert hasattr(log, "send")
    assert hasattr(log, "receive")


def test_logger_send_logs_message(caplog):
    log = logging.getLogger("test_logger_send")
    with caplog.at_level(logger_module.SEND_LEVEL):
        log.send("This is a SEND message")
    assert any("This is a SEND message" in m for m in caplog.messages)
    assert any(r.levelname == "SEND" for r in caplog.records)


def test_logger_receive_logs_message(caplog):
    log = logging.getLogger("test_logger_receive")
    with caplog.at_level(logger_module.RECEIVE_LEVEL):
        log.receive("This is a RECV message")
    assert any("This is a RECV message" in m for m in caplog.messages)
    assert any(r.levelname == "RECV" for r in caplog.records)


def test_logger_verbosity_and_enable_disable(caplog):
    with caplog.at_level(logging.INFO):
        Logger.enable()  # Make sure logging is enabled
        logging.info("This should appear")
        assert "This should appear" in caplog.text
        Logger.disable()
        logging.info("This should NOT appear")
        assert "This should NOT appear" not in caplog.text
        Logger.enable()  # Re-enable for other tests
