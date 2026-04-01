"""Tests for core.logger module."""

import logging

from core.logger import get_logger, log_exception


def test_get_logger_returns_named_logger():
    lg = get_logger("test_module")
    assert lg.name == "AAT.test_module"


def test_get_logger_child_of_aat():
    lg = get_logger("child")
    assert lg.parent is not None
    assert lg.parent.name == "AAT"


def test_log_exception_logs_error(caplog):
    exc = ValueError("boom")
    with caplog.at_level(logging.ERROR, logger="AAT"):
        log_exception(exc, "something failed")
    assert any("boom" in r.message for r in caplog.records)


def test_log_exception_includes_message(caplog):
    exc = RuntimeError("detail")
    with caplog.at_level(logging.ERROR, logger="AAT"):
        log_exception(exc, "custom message")
    assert any("custom message" in r.message for r in caplog.records)


def test_log_exception_default_message(caplog):
    exc = TypeError("bad type")
    with caplog.at_level(logging.ERROR, logger="AAT"):
        log_exception(exc)
    assert any("エラーが発生しました" in r.message for r in caplog.records)
    assert any("bad type" in r.message for r in caplog.records)
