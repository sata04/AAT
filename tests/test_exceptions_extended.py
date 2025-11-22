"""
Tests for custom exception classes in core.exceptions module.

This module provides comprehensive tests for all AAT custom exceptions,
including initialization, attributes, error messages, and inheritance relationships.
"""

import pytest

from core.exceptions import (
    AATException,
    CacheError,
    ColumnNotFoundError,
    ConfigurationError,
    DataLoadError,
    DataProcessingError,
    ExportError,
    InsufficientDataError,
    SyncPointNotFoundError,
)


class TestAATException:
    """Tests for the base AATException class."""

    def test_initialization(self):
        """Test that AATException can be initialized with a message."""
        exc = AATException("Test error message")
        assert str(exc) == "Test error message"

    def test_is_exception(self):
        """Test that AATException is a subclass of Exception."""
        assert issubclass(AATException, Exception)

    def test_can_be_raised(self):
        """Test that AATException can be raised and caught."""
        with pytest.raises(AATException) as exc_info:
            raise AATException("Test exception")
        assert "Test exception" in str(exc_info.value)


class TestDataLoadError:
    """Tests for DataLoadError exception."""

    def test_initialization_with_message_only(self):
        """Test initialization with file_path and message only."""
        exc = DataLoadError("/path/to/file.csv", "Could not read file")
        assert exc.file_path == "/path/to/file.csv"
        assert "データ読み込みエラー" in str(exc)
        assert "/path/to/file.csv" in str(exc)
        assert "Could not read file" in str(exc)

    def test_initialization_with_original_error(self):
        """Test that original_error is stored correctly."""
        original = ValueError("Invalid data")
        exc = DataLoadError("/path/to/file.csv", "Processing failed", original)
        assert exc.original_error is original
        assert exc.file_path == "/path/to/file.csv"

    def test_inherits_from_aat_exception(self):
        """Test that DataLoadError inherits from AATException."""
        assert issubclass(DataLoadError, AATException)


class TestColumnNotFoundError:
    """Tests for ColumnNotFoundError exception."""

    def test_initialization(self):
        """Test initialization with missing and available columns."""
        exc = ColumnNotFoundError(
            "/path/to/file.csv",
            ["time", "acceleration"],
            ["col1", "col2", "col3"],
        )
        assert exc.file_path == "/path/to/file.csv"
        assert exc.missing_columns == ["time", "acceleration"]
        assert exc.available_columns == ["col1", "col2", "col3"]
        assert "必要な列が見つかりません" in str(exc)
        assert "time" in str(exc)
        assert "acceleration" in str(exc)

    def test_inherits_from_data_load_error(self):
        """Test that ColumnNotFoundError inherits from DataLoadError."""
        assert issubclass(ColumnNotFoundError, DataLoadError)

    def test_error_message_format(self):
        """Test the error message format."""
        exc = ColumnNotFoundError(
            "/test.csv",
            ["missing_col"],
            ["available_col"],
        )
        message = str(exc)
        assert "missing_col" in message
        assert "/test.csv" in message


class TestDataProcessingError:
    """Tests for DataProcessingError exception."""

    def test_initialization_without_details(self):
        """Test initialization with message only."""
        exc = DataProcessingError("Processing failed")
        assert exc.details is None
        assert "Processing failed" in str(exc)

    def test_initialization_with_details(self):
        """Test initialization with message and details."""
        exc = DataProcessingError("Processing failed", "Detailed description")
        assert exc.details == "Detailed description"
        assert "Processing failed" in str(exc)
        assert "詳細: Detailed description" in str(exc)

    def test_inherits_from_aat_exception(self):
        """Test that DataProcessingError inherits from AATException."""
        assert issubclass(DataProcessingError, AATException)


class TestSyncPointNotFoundError:
    """Tests for SyncPointNotFoundError exception."""

    def test_initialization(self):
        """Test initialization with sensor type."""
        exc = SyncPointNotFoundError("Inner Capsule")
        assert exc.sensor_type == "Inner Capsule"
        assert "Inner Capsule" in str(exc)
        assert "同期点が見つかりませんでした" in str(exc)

    def test_inherits_from_data_processing_error(self):
        """Test that SyncPointNotFoundError inherits from DataProcessingError."""
        assert issubclass(SyncPointNotFoundError, DataProcessingError)

    def test_different_sensor_types(self):
        """Test with different sensor type names."""
        sensors = ["Inner Capsule", "Drag Shield", "Accelerometer"]
        for sensor in sensors:
            exc = SyncPointNotFoundError(sensor)
            assert sensor in str(exc)


class TestInsufficientDataError:
    """Tests for InsufficientDataError exception."""

    def test_initialization_without_context(self):
        """Test initialization without context."""
        exc = InsufficientDataError(100, 50)
        assert exc.required_length == 100
        assert exc.actual_length == 50
        assert "必要: 100" in str(exc)
        assert "実際: 50" in str(exc)

    def test_initialization_with_context(self):
        """Test initialization with context."""
        exc = InsufficientDataError(100, 50, "統計計算のため")
        assert exc.required_length == 100
        assert exc.actual_length == 50
        assert "統計計算のため" in str(exc)

    def test_inherits_from_data_processing_error(self):
        """Test that InsufficientDataError inherits from DataProcessingError."""
        assert issubclass(InsufficientDataError, DataProcessingError)


class TestConfigurationError:
    """Tests for ConfigurationError exception."""

    def test_initialization_without_config_key(self):
        """Test initialization without config_key."""
        exc = ConfigurationError("Invalid configuration")
        assert exc.config_key is None
        assert "Invalid configuration" in str(exc)

    def test_initialization_with_config_key(self):
        """Test initialization with config_key."""
        exc = ConfigurationError("Value out of range", "sampling_rate")
        assert exc.config_key == "sampling_rate"
        assert "設定エラー [sampling_rate]" in str(exc)
        assert "Value out of range" in str(exc)

    def test_inherits_from_aat_exception(self):
        """Test that ConfigurationError inherits from AATException."""
        assert issubclass(ConfigurationError, AATException)


class TestExportError:
    """Tests for ExportError exception."""

    def test_initialization_without_file_path(self):
        """Test initialization without file_path."""
        exc = ExportError("Export operation failed")
        assert exc.file_path is None
        assert "Export operation failed" in str(exc)

    def test_initialization_with_file_path(self):
        """Test initialization with file_path."""
        exc = ExportError("Cannot write file", "/path/to/output.xlsx")
        assert exc.file_path == "/path/to/output.xlsx"
        assert "エクスポートエラー (/path/to/output.xlsx)" in str(exc)
        assert "Cannot write file" in str(exc)

    def test_inherits_from_aat_exception(self):
        """Test that ExportError inherits from AATException."""
        assert issubclass(ExportError, AATException)


class TestCacheError:
    """Tests for CacheError exception."""

    def test_initialization_without_cache_path(self):
        """Test initialization without cache_path."""
        exc = CacheError("Cache operation failed")
        assert exc.cache_path is None
        assert "Cache operation failed" in str(exc)

    def test_initialization_with_cache_path(self):
        """Test initialization with cache_path."""
        exc = CacheError("Cannot read cache", "/path/to/cache.pickle")
        assert exc.cache_path == "/path/to/cache.pickle"
        assert "キャッシュエラー (/path/to/cache.pickle)" in str(exc)
        assert "Cannot read cache" in str(exc)

    def test_inherits_from_aat_exception(self):
        """Test that CacheError inherits from AATException."""
        assert issubclass(CacheError, AATException)


class TestExceptionInheritanceRelationships:
    """Tests for exception inheritance relationships."""

    def test_all_exceptions_inherit_from_aat_exception(self):
        """Test that all custom exceptions inherit from AATException."""
        exceptions = [
            DataLoadError("/test.csv", "error"),
            ColumnNotFoundError("/test.csv", ["col"], ["other"]),
            DataProcessingError("error"),
            SyncPointNotFoundError("sensor"),
            InsufficientDataError(100, 50),
            ConfigurationError("error"),
            ExportError("error"),
            CacheError("error"),
        ]

        for exc in exceptions:
            assert isinstance(exc, AATException)
            assert isinstance(exc, Exception)

    def test_exception_hierarchy(self):
        """Test the exception hierarchy is correctly established."""
        # DataLoadError hierarchy
        assert issubclass(ColumnNotFoundError, DataLoadError)
        assert issubclass(ColumnNotFoundError, AATException)

        # DataProcessingError hierarchy
        assert issubclass(SyncPointNotFoundError, DataProcessingError)
        assert issubclass(InsufficientDataError, DataProcessingError)
        assert issubclass(DataProcessingError, AATException)

        # Direct AATException subclasses
        assert issubclass(ConfigurationError, AATException)
        assert issubclass(ExportError, AATException)
        assert issubclass(CacheError, AATException)


class TestExceptionRaising:
    """Tests for raising and catching exceptions."""

    def test_can_catch_specific_exception(self):
        """Test that specific exceptions can be caught."""
        with pytest.raises(DataLoadError):
            raise DataLoadError("/test.csv", "error")

    def test_can_catch_with_base_exception(self):
        """Test that exceptions can be caught using base class."""
        with pytest.raises(AATException):
            raise ColumnNotFoundError("/test.csv", ["col"], ["other"])

    def test_exception_chaining(self):
        """Test exception chaining with original_error."""
        original = ValueError("Original error")
        wrapped = DataLoadError("/test.csv", "Wrapped error", original)

        with pytest.raises(DataLoadError) as exc_info:
            raise wrapped

        assert exc_info.value.original_error is original
