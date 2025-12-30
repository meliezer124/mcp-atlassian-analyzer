#!/usr/bin/env python3
"""Manual test script for Phase 3 - Confluence Page Views Analytics."""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from mcp_atlassian.confluence.config import ConfluenceConfig
from mcp_atlassian.confluence import ConfluenceFetcher


def main():
    """Run manual tests for Confluence analytics."""
    # Check for required environment variables
    url = os.getenv("CONFLUENCE_URL")
    username = os.getenv("CONFLUENCE_USERNAME")
    token = os.getenv("CONFLUENCE_API_TOKEN")

    if not all([url, username, token]):
        print("ERROR: Missing Confluence credentials in .env file")
        print("Required: CONFLUENCE_URL, CONFLUENCE_USERNAME, CONFLUENCE_API_TOKEN")
        return 1

    print(f"Confluence URL: {url}")
    print(f"Username: {username}")
    print()

    # Initialize config and fetcher
    config = ConfluenceConfig(
        url=url,
        username=username,
        api_token=token,
        auth_type="basic",
    )

    fetcher = ConfluenceFetcher(config=config)
    print("ConfluenceFetcher initialized successfully!")
    print()

    # Get page ID from user or use default
    page_id = input("Enter a Confluence page ID to test (or press Enter for default): ").strip()
    if not page_id:
        page_id = "40466245"  # Default test page

    print()
    print("=" * 50)
    print("Testing get_page_views")
    print("=" * 50)

    try:
        result = fetcher.get_page_views(page_id=page_id, include_viewers=True)
        print(f"Page ID: {result.page_id}")
        print(f"Page Title: {result.page_title}")
        print(f"Total Views: {result.total_views}")
        print(f"Unique Viewers: {result.unique_viewers}")
        print(f"From Date: {result.from_date}")
        print(f"To Date: {result.to_date}")
    except Exception as e:
        print(f"ERROR: {e}")
        return 1

    print()
    print("=" * 50)
    print("Testing get_page_views with date filter")
    print("=" * 50)

    try:
        result = fetcher.get_page_views(
            page_id=page_id,
            from_date="2024-01-01",
            include_viewers=True
        )
        print(f"Page ID: {result.page_id}")
        print(f"Total Views (since 2024-01-01): {result.total_views}")
        print(f"Unique Viewers: {result.unique_viewers}")
    except Exception as e:
        print(f"ERROR: {e}")

    print()
    print("=" * 50)
    print("Testing batch_get_page_views")
    print("=" * 50)

    try:
        # Test with the same page (in real usage, you'd use multiple pages)
        result = fetcher.batch_get_page_views(
            page_ids=[page_id],
            include_viewers=True
        )
        print(f"Total Count: {result.total_count}")
        print(f"Success Count: {result.success_count}")
        print(f"Error Count: {result.error_count}")
        if result.pages:
            print(f"First Page Views: {result.pages[0].total_views}")
        if result.errors:
            print(f"Errors: {result.errors}")
    except Exception as e:
        print(f"ERROR: {e}")
        return 1

    print()
    print("All tests completed successfully!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
