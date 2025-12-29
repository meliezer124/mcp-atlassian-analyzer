"""Module for Confluence analytics operations.

This module provides analytics functionality for Confluence pages,
including view counts and viewer information.

Note: The Confluence Analytics API is only available on Cloud instances.
Server/Data Center deployments do not support this feature.
"""

import logging
from datetime import datetime, timezone

from requests.exceptions import HTTPError

from ..exceptions import MCPAtlassianAuthenticationError
from ..models.confluence import (
    AnalyticsNotAvailableError,
    PageViewsBatchResponse,
    PageViewsResponse,
)
from .client import ConfluenceClient
from .v2_adapter import ConfluenceV2Adapter

logger = logging.getLogger("mcp-atlassian")


class AnalyticsMixin(ConfluenceClient):
    """Mixin for Confluence analytics operations.

    Provides methods to retrieve page view statistics and viewer information.
    These features are only available on Confluence Cloud.
    """

    @property
    def _analytics_adapter(self) -> ConfluenceV2Adapter:
        """Get the v2 adapter for analytics API calls.

        The analytics API uses the same base URL structure as the v2 API
        but is accessed via v1 endpoints (/rest/api/analytics/...).

        Returns:
            ConfluenceV2Adapter instance

        Raises:
            AnalyticsNotAvailableError: If not on Confluence Cloud
        """
        if not self.config.is_cloud:
            raise AnalyticsNotAvailableError(
                "Confluence Analytics API is only available on Cloud instances. "
                "Server/Data Center deployments do not support this feature."
            )

        return ConfluenceV2Adapter(
            session=self.confluence._session, base_url=self.confluence.url
        )

    def get_page_views(
        self,
        page_id: str,
        from_date: str | None = None,
        *,
        include_viewers: bool = True,
    ) -> PageViewsResponse:
        """Get view statistics for a Confluence page.

        Retrieves the total number of views and optionally the number of
        unique viewers for a specific page.

        Args:
            page_id: The ID of the page to get views for
            from_date: Optional start date (ISO format: YYYY-MM-DD)
            include_viewers: Whether to also fetch unique viewer count (default: True)

        Returns:
            PageViewsResponse containing view and viewer counts

        Raises:
            AnalyticsNotAvailableError: If analytics API is not available (Server/DC)
            MCPAtlassianAuthenticationError: If authentication fails (401/403)
            ValueError: If the API call fails for other reasons
        """
        try:
            adapter = self._analytics_adapter

            # Get view count
            views_data = adapter.get_content_views(page_id, from_date=from_date)
            total_views = views_data.get("count", 0)

            # Get viewer count if requested
            unique_viewers = 0
            if include_viewers:
                viewers_data = adapter.get_content_viewers(page_id, from_date=from_date)
                unique_viewers = viewers_data.get("count", 0)

            # Try to get page title
            page_title = None
            try:
                page = self.confluence.get_page_by_id(page_id)
                if page:
                    page_title = page.get("title")
            except (ValueError, KeyError, AttributeError) as e:
                logger.debug(f"Could not fetch page title for {page_id}: {e}")

            # Calculate to_date as today if not provided
            to_date = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d")

            return PageViewsResponse(
                page_id=page_id,
                page_title=page_title,
                total_views=total_views,
                unique_viewers=unique_viewers,
                from_date=from_date,
                to_date=to_date,
            )

        except AnalyticsNotAvailableError:
            raise
        except HTTPError as http_err:
            if http_err.response is not None and http_err.response.status_code in [
                401,
                403,
            ]:
                error_msg = (
                    f"Authentication failed for Confluence Analytics API "
                    f"({http_err.response.status_code}). "
                    "Token may be expired or invalid, or you may not have "
                    "permission to access analytics."
                )
                logger.error(error_msg)
                raise MCPAtlassianAuthenticationError(error_msg) from http_err
            raise
        except Exception as e:
            logger.error(f"Error getting page views for {page_id}: {e}")
            raise

    def batch_get_page_views(
        self,
        page_ids: list[str],
        from_date: str | None = None,
        *,
        include_viewers: bool = True,
    ) -> PageViewsBatchResponse:
        """Get view statistics for multiple Confluence pages.

        Retrieves analytics data for a batch of pages. Errors for individual
        pages are captured but don't stop processing of other pages.

        Args:
            page_ids: List of page IDs to get views for
            from_date: Optional start date (ISO format: YYYY-MM-DD)
            include_viewers: Whether to also fetch unique viewer count (default: True)

        Returns:
            PageViewsBatchResponse containing results and any errors

        Raises:
            AnalyticsNotAvailableError: If analytics API is not available (Server/DC)
        """
        # Check Cloud availability once before processing
        if not self.config.is_cloud:
            raise AnalyticsNotAvailableError(
                "Confluence Analytics API is only available on Cloud instances. "
                "Server/Data Center deployments do not support this feature."
            )

        pages: list[PageViewsResponse] = []
        errors: list[dict[str, str]] = []
        to_date = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d")

        for page_id in page_ids:
            try:
                result = self.get_page_views(
                    page_id=page_id,
                    from_date=from_date,
                    include_viewers=include_viewers,
                )
                pages.append(result)
            except (ValueError, AnalyticsNotAvailableError) as e:
                errors.append({
                    "page_id": page_id,
                    "error": str(e),
                })
                logger.warning(f"Failed to get views for page {page_id}: {e}")

        return PageViewsBatchResponse(
            pages=pages,
            total_count=len(page_ids),
            success_count=len(pages),
            error_count=len(errors),
            errors=errors,
            from_date=from_date,
            to_date=to_date,
        )
