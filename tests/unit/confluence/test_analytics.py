"""Tests for the Confluence Analytics mixin."""

from unittest.mock import MagicMock, patch

import pytest

from mcp_atlassian.confluence.analytics import AnalyticsMixin
from mcp_atlassian.models.confluence import (
    AnalyticsNotAvailableError,
    PageViewsBatchResponse,
    PageViewsResponse,
)


class TestAnalyticsModels:
    """Tests for the analytics Pydantic models."""

    def test_page_views_response_creation(self):
        """Test PageViewsResponse model creation."""
        response = PageViewsResponse(
            page_id="123456",
            page_title="Test Page",
            total_views=100,
            unique_viewers=25,
            from_date="2023-01-01",
            to_date="2023-12-31",
        )

        assert response.page_id == "123456"
        assert response.page_title == "Test Page"
        assert response.total_views == 100
        assert response.unique_viewers == 25
        assert response.from_date == "2023-01-01"
        assert response.to_date == "2023-12-31"

    def test_page_views_response_to_simplified_dict(self):
        """Test PageViewsResponse serialization."""
        response = PageViewsResponse(
            page_id="123456",
            page_title="Test Page",
            total_views=100,
            unique_viewers=25,
            from_date="2023-01-01",
        )

        result = response.to_simplified_dict()

        assert result["page_id"] == "123456"
        assert result["page_title"] == "Test Page"
        assert result["total_views"] == 100
        assert result["unique_viewers"] == 25
        assert result["from_date"] == "2023-01-01"
        assert "to_date" not in result  # None values should be excluded

    def test_page_views_response_without_optional_fields(self):
        """Test PageViewsResponse with minimal fields."""
        response = PageViewsResponse(
            page_id="123456",
            total_views=50,
            unique_viewers=10,
        )

        result = response.to_simplified_dict()

        assert result["page_id"] == "123456"
        assert result["total_views"] == 50
        assert result["unique_viewers"] == 10
        assert "page_title" not in result
        assert "from_date" not in result

    def test_page_views_response_from_api_response(self):
        """Test creating PageViewsResponse from API data."""
        api_data = {"count": 150}
        result = PageViewsResponse.from_api_response(
            api_data,
            page_id="789",
            page_title="API Page",
            from_date="2023-06-01",
        )

        assert result.page_id == "789"
        assert result.page_title == "API Page"
        assert result.total_views == 150
        assert result.from_date == "2023-06-01"

    def test_page_views_batch_response_creation(self):
        """Test PageViewsBatchResponse model creation."""
        pages = [
            PageViewsResponse(page_id="1", total_views=100, unique_viewers=20),
            PageViewsResponse(page_id="2", total_views=200, unique_viewers=40),
        ]

        batch = PageViewsBatchResponse(
            pages=pages,
            total_count=3,
            success_count=2,
            error_count=1,
            errors=[{"page_id": "3", "error": "Not found"}],
            from_date="2023-01-01",
        )

        assert batch.total_count == 3
        assert batch.success_count == 2
        assert batch.error_count == 1
        assert len(batch.pages) == 2
        assert len(batch.errors) == 1

    def test_page_views_batch_response_to_simplified_dict(self):
        """Test PageViewsBatchResponse serialization."""
        pages = [
            PageViewsResponse(page_id="1", total_views=100, unique_viewers=20),
        ]

        batch = PageViewsBatchResponse(
            pages=pages,
            total_count=2,
            success_count=1,
            error_count=1,
            errors=[{"page_id": "2", "error": "Error"}],
        )

        result = batch.to_simplified_dict()

        assert result["total_count"] == 2
        assert result["success_count"] == 1
        assert result["error_count"] == 1
        assert len(result["pages"]) == 1
        assert len(result["errors"]) == 1


class TestAnalyticsMixin:
    """Tests for the AnalyticsMixin class."""

    def test_analytics_not_available_on_server(self):
        """Test that analytics raises error on Server/DC."""
        # Create a mixin-like object with server config
        mixin = MagicMock()
        mixin.config = MagicMock()
        mixin.config.is_cloud = False

        # Test the property directly by calling the getter function
        with pytest.raises(AnalyticsNotAvailableError) as exc_info:
            AnalyticsMixin._analytics_adapter.fget(mixin)

        assert "Cloud" in str(exc_info.value)
        assert "Server/Data Center" in str(exc_info.value)

    def test_get_page_views_cloud_success(self):
        """Test successful page view retrieval on Cloud."""
        # Create a mock adapter with proper return values
        mock_adapter = MagicMock()
        mock_adapter.get_content_views.return_value = {"count": 150}
        mock_adapter.get_content_viewers.return_value = {"count": 30}

        patch_target = "mcp_atlassian.confluence.analytics.ConfluenceV2Adapter"
        with patch(patch_target) as adapter_class:
            adapter_class.return_value = mock_adapter

            # Create a class that includes the property
            class MockMixin:
                @property
                def _analytics_adapter(self):
                    return adapter_class()

            mixin = MockMixin()
            mixin.config = MagicMock()
            mixin.config.is_cloud = True
            mixin.confluence = MagicMock()
            mixin.confluence._session = MagicMock()
            mixin.confluence.url = "https://example.atlassian.net/wiki"
            mixin.confluence.get_page_by_id.return_value = {"title": "Test Page"}

            # Call the real get_page_views method
            result = AnalyticsMixin.get_page_views(
                mixin,
                page_id="123456",
                from_date="2023-01-01",
                include_viewers=True,
            )

            assert result.page_id == "123456"
            assert result.total_views == 150
            assert result.unique_viewers == 30
            assert result.from_date == "2023-01-01"
            mock_adapter.get_content_views.assert_called_once()
            mock_adapter.get_content_viewers.assert_called_once()

    def test_get_page_views_without_viewers(self):
        """Test page view retrieval without fetching viewers."""
        mock_adapter = MagicMock()
        mock_adapter.get_content_views.return_value = {"count": 100}

        patch_target = "mcp_atlassian.confluence.analytics.ConfluenceV2Adapter"
        with patch(patch_target) as adapter_class:
            adapter_class.return_value = mock_adapter

            class MockMixin:
                @property
                def _analytics_adapter(self):
                    return adapter_class()

            mixin = MockMixin()
            mixin.config = MagicMock()
            mixin.config.is_cloud = True
            mixin.confluence = MagicMock()
            mixin.confluence._session = MagicMock()
            mixin.confluence.url = "https://example.atlassian.net/wiki"
            mixin.confluence.get_page_by_id.return_value = None

            result = AnalyticsMixin.get_page_views(
                mixin,
                page_id="123456",
                include_viewers=False,
            )

            assert result.total_views == 100
            assert result.unique_viewers == 0
            mock_adapter.get_content_viewers.assert_not_called()

    def test_batch_get_page_views_success(self):
        """Test batch page view retrieval."""
        mixin = MagicMock()
        mixin.config = MagicMock()
        mixin.config.is_cloud = True
        mixin.confluence = MagicMock()
        mixin.confluence._session = MagicMock()
        mixin.confluence.url = "https://example.atlassian.net/wiki"
        mixin.confluence.get_page_by_id.return_value = None

        # Mock the get_page_views method to return proper objects
        # since batch_get_page_views calls self.get_page_views
        def mock_get_page_views(page_id, from_date=None, *, include_viewers=True):
            return PageViewsResponse(
                page_id=page_id,
                total_views=50,
                unique_viewers=10 if include_viewers else 0,
                from_date=from_date,
            )

        mixin.get_page_views = mock_get_page_views

        result = AnalyticsMixin.batch_get_page_views(
            mixin,
            page_ids=["1", "2", "3"],
            from_date="2023-01-01",
        )

        assert result.total_count == 3
        assert result.success_count == 3
        assert result.error_count == 0
        assert len(result.pages) == 3

    def test_batch_get_page_views_with_errors(self):
        """Test batch page view retrieval with some errors."""

        def mock_get_page_views(page_id, from_date=None, *, include_viewers=True):
            if page_id == "2":
                raise ValueError("Page not found")
            return PageViewsResponse(
                page_id=page_id,
                total_views=50,
                unique_viewers=10,
                from_date=from_date,
            )

        mixin = MagicMock()
        mixin.config = MagicMock()
        mixin.config.is_cloud = True
        mixin.get_page_views = mock_get_page_views

        result = AnalyticsMixin.batch_get_page_views(
            mixin,
            page_ids=["1", "2", "3"],
        )

        assert result.total_count == 3
        assert result.success_count == 2
        assert result.error_count == 1
        assert len(result.errors) == 1
        assert result.errors[0]["page_id"] == "2"

    def test_batch_get_page_views_server_error(self):
        """Test batch operation fails immediately on Server/DC."""
        mixin = MagicMock()
        mixin.config = MagicMock()
        mixin.config.is_cloud = False

        with pytest.raises(AnalyticsNotAvailableError):
            AnalyticsMixin.batch_get_page_views(mixin, page_ids=["1", "2"])


class TestAnalyticsNotAvailableError:
    """Tests for the AnalyticsNotAvailableError exception."""

    def test_error_creation(self):
        """Test creating the error with a message."""
        error = AnalyticsNotAvailableError("Analytics not available")
        assert str(error) == "Analytics not available"

    def test_error_inheritance(self):
        """Test that the error inherits from Exception."""
        error = AnalyticsNotAvailableError("Test")
        assert isinstance(error, Exception)

    def test_error_can_be_raised_and_caught(self):
        """Test that the error can be properly raised and caught."""
        with pytest.raises(AnalyticsNotAvailableError) as exc_info:
            raise AnalyticsNotAvailableError("Cloud only feature")

        assert "Cloud only" in str(exc_info.value)
