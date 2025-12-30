# MCP Atlassian Analyzer

Analytics and SLA metrics extension for the [MCP Atlassian](https://github.com/sooperset/mcp-atlassian) server.

This fork adds powerful analytics and workflow intelligence tools to help teams understand content engagement, measure SLA compliance, and optimize their Atlassian workflows.

## What's New in This Fork

| Tool | Description | Platform |
|------|-------------|----------|
| `jira_get_issue_dates` | Extract raw dates and status transition history | Cloud & Server |
| `jira_get_issue_sla` | Calculate SLA metrics (cycle time, lead time, etc.) | Cloud & Server |
| `confluence_get_page_views` | Get page view counts and unique viewers | Cloud only |
| `confluence_get_page_analytics` | Calculate engagement metrics for pages | Cloud only |
| `confluence_get_space_analytics` | Aggregate analytics across a Confluence space | Cloud only |

> **Base Features**: For core Confluence and Jira operations (search, create, update, etc.), see the [upstream MCP Atlassian documentation](https://github.com/sooperset/mcp-atlassian).

---

## Use Cases

### Jira Workflow Analysis

**"How long do issues spend in each status?"**
```
Use jira_get_issue_sla with metrics=time_in_status to see exactly how long
issues stay in "In Progress", "Code Review", "QA", etc.
```

**"Are we meeting our SLA targets?"**
```
Use jira_get_issue_sla with metrics=cycle_time,due_date_compliance to measure
actual delivery time vs commitments.
```

**"What's our team's velocity trend?"**
```
Use jira_get_issue_dates on resolved issues to analyze resolution patterns
and identify bottlenecks in your workflow.
```

### Confluence Content Health

**"Which pages need attention?"**
```
Use confluence_get_space_analytics with include_stale_pages=true to find
content that hasn't been viewed in 90+ days.
```

**"What content is most valuable to the team?"**
```
Use confluence_get_space_analytics with include_popular_pages=true to identify
your most-viewed documentation.
```

**"Is our documentation being used?"**
```
Use confluence_get_page_analytics to calculate engagement scores based on
views, unique viewers, and recency.
```

---

## Installation & Setup

### Prerequisites

Follow the [upstream installation guide](https://github.com/sooperset/mcp-atlassian#quick-start-guide) for:
- Docker setup
- Atlassian authentication (API tokens or OAuth)
- IDE integration (Claude Desktop, Cursor, etc.)

### Using This Fork

Replace the upstream Docker image with this fork:

```json
{
  "mcpServers": {
    "mcp-atlassian": {
      "command": "docker",
      "args": [
        "run", "-i", "--rm",
        "-e", "CONFLUENCE_URL",
        "-e", "CONFLUENCE_USERNAME",
        "-e", "CONFLUENCE_API_TOKEN",
        "-e", "JIRA_URL",
        "-e", "JIRA_USERNAME",
        "-e", "JIRA_API_TOKEN",
        "ghcr.io/meliezer124/mcp-atlassian-analyzer:latest"
      ],
      "env": {
        "CONFLUENCE_URL": "https://your-company.atlassian.net/wiki",
        "CONFLUENCE_USERNAME": "your.email@company.com",
        "CONFLUENCE_API_TOKEN": "your_confluence_api_token",
        "JIRA_URL": "https://your-company.atlassian.net",
        "JIRA_USERNAME": "your.email@company.com",
        "JIRA_API_TOKEN": "your_jira_api_token"
      }
    }
  }
}
```

---

## Tool Reference

### Jira Tools

#### `jira_get_issue_dates`

Extract raw date fields and complete status transition history from Jira issues.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `issue_key` | string | Yes* | Single issue key (e.g., "PROJ-123") |
| `issue_keys` | string | Yes* | Comma-separated keys for batch operations |
| `include_changelog` | boolean | No | Include status change history (default: true) |
| `include_time_in_status` | boolean | No | Calculate time spent in each status (default: true) |

*Provide either `issue_key` or `issue_keys`

**Example Response:**
```json
{
  "issue_key": "PROJ-123",
  "created": "2024-01-15T09:00:00.000+0000",
  "updated": "2024-01-20T14:30:00.000+0000",
  "resolution_date": "2024-01-20T14:30:00.000+0000",
  "due_date": "2024-01-22",
  "status_changes": [
    {
      "status": "To Do",
      "entered_at": "2024-01-15T09:00:00.000+0000",
      "exited_at": "2024-01-16T10:00:00.000+0000",
      "duration_minutes": 1500,
      "duration_formatted": "1d 1h 0m"
    },
    {
      "status": "In Progress",
      "entered_at": "2024-01-16T10:00:00.000+0000",
      "exited_at": "2024-01-20T14:30:00.000+0000",
      "duration_minutes": 5910,
      "duration_formatted": "4d 2h 30m"
    }
  ],
  "time_in_status": {
    "To Do": "1d 1h 0m",
    "In Progress": "4d 2h 30m",
    "Done": "0m (current)"
  }
}
```

---

#### `jira_get_issue_sla`

Calculate SLA metrics based on issue dates and status transitions.

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `issue_key` | string | Yes* | - | Single issue key |
| `issue_keys` | string | Yes* | - | Comma-separated keys for batch |
| `metrics` | string | No | From config | Comma-separated metrics to calculate |
| `working_hours_only` | boolean | No | false | Exclude weekends/non-business hours |

*Provide either `issue_key` or `issue_keys`

**Available Metrics:**

| Metric | Description |
|--------|-------------|
| `cycle_time` | Time from "In Progress" to "Done" |
| `lead_time` | Time from creation to resolution |
| `time_in_status` | Breakdown by status |
| `due_date_compliance` | Whether resolved before due date |
| `resolution_time` | Time from creation to resolution |
| `first_response_time` | Time to first status change |

**Example Response:**
```json
{
  "issue_key": "PROJ-123",
  "metrics": {
    "cycle_time": {
      "value_minutes": 5910,
      "formatted": "4d 2h 30m",
      "start_status": "In Progress",
      "end_status": "Done"
    },
    "lead_time": {
      "value_minutes": 7410,
      "formatted": "5d 3h 30m"
    },
    "due_date_compliance": {
      "status": "met",
      "due_date": "2024-01-22",
      "resolution_date": "2024-01-20",
      "days_remaining": 2
    },
    "time_in_status": {
      "To Do": 1500,
      "In Progress": 5910,
      "Done": 0
    }
  }
}
```

---

### Confluence Tools

#### `confluence_get_page_views`

Get view statistics for Confluence pages.

> **Note:** This tool requires Confluence Cloud. Server/Data Center does not support the Analytics API.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `page_id` | string | Yes* | Single page ID |
| `page_ids` | string | Yes* | Comma-separated IDs for batch |
| `from_date` | string | No | Start date (YYYY-MM-DD), defaults to all-time |
| `include_viewers` | boolean | No | Include unique viewer count (default: true) |

*Provide either `page_id` or `page_ids`

**Example Response:**
```json
{
  "page_id": "123456789",
  "total_views": 1250,
  "unique_viewers": 89,
  "from_date": "2024-01-01",
  "to_date": "2024-01-31"
}
```

---

#### `confluence_get_page_analytics`

Calculate engagement metrics for Confluence pages based on view data.

> **Note:** This tool requires Confluence Cloud.

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `page_id` | string | Yes* | - | Single page ID |
| `page_ids` | string | Yes* | - | Comma-separated IDs for batch |
| `metrics` | string | No | From config | Metrics to calculate |
| `period_days` | integer | No | 30 | Analysis period (1-365 days) |
| `include_raw_data` | boolean | No | false | Include raw view counts |

*Provide either `page_id` or `page_ids`

**Available Metrics:**

| Metric | Description | Values |
|--------|-------------|--------|
| `engagement_score` | Composite score (0-100) based on views, viewers, recency | 0-100 |
| `view_velocity` | Trend in view activity | `increasing`, `stable`, `decreasing` |
| `staleness` | Content freshness indicator | `active`, `stale`, `abandoned` |
| `viewer_diversity` | Breadth of audience | `narrow`, `moderate`, `broad` |

**Example Response:**
```json
{
  "page_id": "123456789",
  "period_days": 30,
  "metrics": {
    "engagement_score": {
      "value": 72,
      "interpretation": "high",
      "components": {
        "view_score": 85,
        "viewer_score": 60,
        "recency_score": 70
      }
    },
    "view_velocity": {
      "trend": "increasing",
      "change_percent": 25.5
    },
    "staleness": {
      "status": "active",
      "days_since_last_view": 2
    },
    "viewer_diversity": {
      "interpretation": "moderate",
      "unique_viewer_ratio": 0.45
    }
  }
}
```

---

#### `confluence_get_space_analytics`

Get aggregated analytics across all pages in a Confluence space.

> **Note:** This tool requires Confluence Cloud.

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `space_key` | string | Yes | - | Space key (e.g., "DEV", "TEAM") |
| `period_days` | integer | No | 30 | Analysis period (1-365 days) |
| `limit` | integer | No | 10 | Max pages per category (1-50) |
| `stale_threshold_days` | integer | No | 90 | Days without views = stale |
| `include_summary` | boolean | No | true | Include space-level stats |
| `include_popular_pages` | boolean | No | true | Top pages by views |
| `include_trending_pages` | boolean | No | true | Pages with increasing velocity |
| `include_stale_pages` | boolean | No | true | Pages needing attention |

**Example Response:**
```json
{
  "space_key": "DEV",
  "space_name": "Development",
  "period_days": 30,
  "summary": {
    "total_pages": 150,
    "pages_analyzed": 150,
    "total_views": 4523,
    "total_unique_viewers": 89,
    "average_views_per_page": 30.2,
    "average_engagement_score": 45.8,
    "active_pages_count": 82,
    "stale_pages_count": 45,
    "abandoned_pages_count": 23
  },
  "popular_pages": [
    {
      "page_id": "123456",
      "page_title": "Getting Started Guide",
      "total_views": 892,
      "unique_viewers": 67,
      "engagement_score": 95
    }
  ],
  "trending_pages": [
    {
      "page_id": "789012",
      "page_title": "New Feature Documentation",
      "trend": "increasing",
      "change_percent": 150.0
    }
  ],
  "stale_pages": [
    {
      "page_id": "345678",
      "page_title": "Old Process Guide",
      "staleness_status": "abandoned",
      "days_since_last_view": 180
    }
  ]
}
```

---

## Configuration

### Environment Variables

Add these to your `.env` file or pass via Docker `-e` flags:

#### Jira SLA Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `JIRA_SLA_METRICS` | `cycle_time,time_in_status` | Default metrics to calculate |
| `JIRA_SLA_WORKING_HOURS_ONLY` | `false` | Exclude non-working hours |
| `JIRA_SLA_WORKING_HOURS_START` | `09:00` | Business day start (24h format) |
| `JIRA_SLA_WORKING_HOURS_END` | `17:00` | Business day end (24h format) |
| `JIRA_SLA_WORKING_DAYS` | `1,2,3,4,5` | Working days (1=Mon, 7=Sun) |
| `JIRA_SLA_TIMEZONE` | `UTC` | Timezone for calculations |

#### Confluence Analytics Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `CONFLUENCE_ANALYTICS_METRICS` | `engagement_score,staleness` | Default metrics |
| `CONFLUENCE_ANALYTICS_PERIOD_DAYS` | `30` | Default analysis period |

### Example Configuration

```bash
# .env file

# Jira SLA - Calculate working hours only (9-5, Mon-Fri, EST)
JIRA_SLA_WORKING_HOURS_ONLY=true
JIRA_SLA_WORKING_HOURS_START=09:00
JIRA_SLA_WORKING_HOURS_END=17:00
JIRA_SLA_WORKING_DAYS=1,2,3,4,5
JIRA_SLA_TIMEZONE=America/New_York
JIRA_SLA_METRICS=cycle_time,lead_time,time_in_status,due_date_compliance

# Confluence Analytics - 90-day analysis with all metrics
CONFLUENCE_ANALYTICS_PERIOD_DAYS=90
CONFLUENCE_ANALYTICS_METRICS=engagement_score,view_velocity,staleness,viewer_diversity
```

---

## Platform Compatibility

| Tool | Confluence Cloud | Confluence Server/DC | Jira Cloud | Jira Server/DC |
|------|-----------------|---------------------|------------|----------------|
| `jira_get_issue_dates` | - | - | Yes | Yes |
| `jira_get_issue_sla` | - | - | Yes | Yes |
| `confluence_get_page_views` | Yes | No | - | - |
| `confluence_get_page_analytics` | Yes | No | - | - |
| `confluence_get_space_analytics` | Yes | No | - | - |

> **Why Cloud only for Confluence Analytics?** The Confluence Analytics API is only available on Cloud instances. Server/Data Center deployments do not expose view statistics through their REST API.

---

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

Licensed under MIT - see [LICENSE](LICENSE) file.

---

## Acknowledgments

This project is a fork of [MCP Atlassian](https://github.com/sooperset/mcp-atlassian) by sooperset. The base MCP server functionality and core Atlassian integrations come from that project.
