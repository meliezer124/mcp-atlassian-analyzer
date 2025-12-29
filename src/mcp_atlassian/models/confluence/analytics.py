"""
Analytics data models for Confluence page views and engagement metrics.

This module provides Pydantic models for Confluence Analytics API responses,
including page view counts, viewer information, and batch operations.

Note: These analytics endpoints are only available on Confluence Cloud.
"""

from typing import Any

from pydantic import Field

from ..base import ApiModel


class PageViewsResponse(ApiModel):
    """
    Model representing page view analytics for a single Confluence page.

    Contains view count, viewer count, and metadata about the page.
    """

    page_id: str = Field(description="The Confluence page ID")
    page_title: str | None = Field(
        default=None,
        description="The page title (if available)"
    )
    total_views: int = Field(
        default=0,
        description="Total number of views for the page"
    )
    unique_viewers: int = Field(
        default=0,
        description="Number of unique viewers"
    )
    from_date: str | None = Field(
        default=None,
        description="Start date for the analytics period (ISO format)"
    )
    to_date: str | None = Field(
        default=None,
        description="End date for the analytics period (ISO format)"
    )

    @classmethod
    def from_api_response(
        cls, data: dict[str, Any], **kwargs: Any
    ) -> "PageViewsResponse":
        """Create a PageViewsResponse from API data.

        Args:
            data: Dictionary containing views and viewers data
            **kwargs: Additional context (page_id, page_title, from_date, to_date)

        Returns:
            PageViewsResponse instance
        """
        return cls(
            page_id=kwargs.get("page_id", data.get("id", "")),
            page_title=kwargs.get("page_title"),
            total_views=data.get("count", 0),
            unique_viewers=data.get("viewers", 0),
            from_date=kwargs.get("from_date"),
            to_date=kwargs.get("to_date"),
        )

    def to_simplified_dict(self) -> dict[str, Any]:
        """Convert to simplified dictionary for API response."""
        result: dict[str, Any] = {
            "page_id": self.page_id,
            "total_views": self.total_views,
            "unique_viewers": self.unique_viewers,
        }
        if self.page_title:
            result["page_title"] = self.page_title
        if self.from_date:
            result["from_date"] = self.from_date
        if self.to_date:
            result["to_date"] = self.to_date
        return result


class PageViewsBatchResponse(ApiModel):
    """
    Model representing batch page views response for multiple pages.

    Wraps multiple PageViewsResponse objects with metadata
    about the batch operation.
    """

    pages: list[PageViewsResponse] = Field(
        default_factory=list,
        description="List of page view responses"
    )
    total_count: int = Field(
        default=0,
        description="Total number of pages processed"
    )
    success_count: int = Field(
        default=0,
        description="Number of pages successfully processed"
    )
    error_count: int = Field(
        default=0,
        description="Number of pages that failed to process"
    )
    errors: list[dict[str, str]] = Field(
        default_factory=list,
        description="List of errors for failed pages"
    )
    from_date: str | None = Field(
        default=None,
        description="Start date for the analytics period"
    )
    to_date: str | None = Field(
        default=None,
        description="End date for the analytics period"
    )

    @classmethod
    def from_api_response(
        cls, data: dict[str, Any], **kwargs: Any
    ) -> "PageViewsBatchResponse":
        """Create a PageViewsBatchResponse from data."""
        pages = [
            PageViewsResponse.from_api_response(page)
            for page in data.get("pages", [])
        ]
        return cls(
            pages=pages,
            total_count=data.get("total_count", len(pages)),
            success_count=data.get("success_count", len(pages)),
            error_count=data.get("error_count", 0),
            errors=data.get("errors", []),
            from_date=data.get("from_date"),
            to_date=data.get("to_date"),
        )

    def to_simplified_dict(self) -> dict[str, Any]:
        """Convert to simplified dictionary for API response."""
        result: dict[str, Any] = {
            "total_count": self.total_count,
            "success_count": self.success_count,
            "error_count": self.error_count,
            "pages": [page.to_simplified_dict() for page in self.pages],
        }
        if self.errors:
            result["errors"] = self.errors
        if self.from_date:
            result["from_date"] = self.from_date
        if self.to_date:
            result["to_date"] = self.to_date
        return result


class AnalyticsNotAvailableError(Exception):
    """Exception raised when analytics API is not available.

    This typically happens when:
    - Using Confluence Server/Data Center (analytics is Cloud-only)
    - The user doesn't have the required permissions
    """

    pass
