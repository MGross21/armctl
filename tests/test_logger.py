import logging

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
    armctl_logger = logging.getLogger("armctl.test")
    with caplog.at_level(logging.INFO):
        Logger.enable()  # Make sure logging is enabled
        armctl_logger.info("This should appear")
        assert "This should appear" in caplog.text
        Logger.disable()
        armctl_logger.info("This should NOT appear")
        assert "This should NOT appear" not in caplog.text
        Logger.enable()  # Re-enable for other tests


def test_rtde_logger_suppression(caplog):
    """Test that the RTDE logger is suppressed when Logger.disable() is called."""
    rtde_logger = logging.getLogger("rtde")
    
    # Enable logging first
    Logger.enable()
    with caplog.at_level(logging.INFO):
        rtde_logger.info("RTDE message when enabled")
    assert "RTDE message when enabled" in caplog.text
    
    # Clear captured logs
    caplog.clear()
    
    # Disable logging and test that RTDE logger is suppressed
    Logger.disable()
    with caplog.at_level(logging.INFO):
        rtde_logger.info("RTDE message when disabled")
    assert "RTDE message when disabled" not in caplog.text
    
    # Re-enable for other tests
    Logger.enable()


def test_other_loggers_not_affected(caplog):
    """Test that non-armctl loggers are NOT affected by Logger.disable()."""
    other_logger = logging.getLogger("some.other.library")
    
    Logger.enable()
    with caplog.at_level(logging.INFO):
        other_logger.info("Other library message when enabled")
    assert "Other library message when enabled" in caplog.text
    
    caplog.clear()
    
    # Disable armctl logging - should NOT affect other loggers
    Logger.disable()
    with caplog.at_level(logging.INFO):
        other_logger.info("Other library message when disabled")
    assert "Other library message when disabled" in caplog.text
    
    Logger.enable()

