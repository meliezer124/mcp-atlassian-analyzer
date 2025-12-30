#!/usr/bin/env python3
"""Manual test script for Phase 4 - Confluence Page Analytics (Calculated Metrics)."""

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
    """Run manual tests for Confluence page analytics."""
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
    print("=" * 60)
    print("Testing get_page_analytics (default metrics)")
    print("=" * 60)

    try:
        result = fetcher.get_page_analytics(
            page_id=page_id,
            include_raw_data=True,
        )
        print(f"Page ID: {result.page_id}")
        print(f"Page Title: {result.page_title}")
        print(f"Period Days: {result.period_days}")
        print()
        print("Metrics:")
        for metric_name, metric_value in result.metrics.items():
            print(f"  {metric_name}:")
            simplified = metric_value.to_simplified_dict()
            for key, value in simplified.items():
                print(f"    {key}: {value}")
        print()
        if result.raw_data:
            print("Raw Data:")
            for key, value in result.raw_data.items():
                print(f"  {key}: {value}")
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1

    print()
    print("=" * 60)
    print("Testing get_page_analytics (all metrics)")
    print("=" * 60)

    try:
        result = fetcher.get_page_analytics(
            page_id=page_id,
            metrics=["engagement_score", "view_velocity", "staleness", "viewer_diversity"],
            period_days=60,
            include_raw_data=True,
        )
        print(f"Page ID: {result.page_id}")
        print(f"Period Days: {result.period_days}")
        print()
        print("Metrics:")
        for metric_name, metric_value in result.metrics.items():
            print(f"  {metric_name}:")
            simplified = metric_value.to_simplified_dict()
            for key, value in simplified.items():
                print(f"    {key}: {value}")
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

    print()
    print("=" * 60)
    print("Testing batch_get_page_analytics")
    print("=" * 60)

    try:
        # Test with the same page (in real usage, you'd use multiple pages)
        result = fetcher.batch_get_page_analytics(
            page_ids=[page_id],
            metrics=["engagement_score", "staleness"],
            include_raw_data=False,
        )
        print(f"Total Count: {result.total_count}")
        print(f"Success Count: {result.success_count}")
        print(f"Error Count: {result.error_count}")
        print(f"Metrics Calculated: {result.metrics_calculated}")
        if result.pages:
            print(f"First Page Engagement Score: {result.pages[0].metrics.get('engagement_score')}")
        if result.errors:
            print(f"Errors: {result.errors}")
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1

    print()
    print("=" * 60)
    print("Testing serialization (to_simplified_dict)")
    print("=" * 60)

    try:
        result = fetcher.get_page_analytics(
            page_id=page_id,
            metrics=["engagement_score"],
            include_raw_data=True,
        )
        simplified = result.to_simplified_dict()
        import json
        print(json.dumps(simplified, indent=2))
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1

    print()
    print("All tests completed successfully!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
