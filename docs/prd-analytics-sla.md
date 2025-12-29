# PRD: Analytics & SLA Metrics for MCP Atlassian

## Document Info

| Field | Value |
|-------|-------|
| **Version** | 1.0 |
| **Created** | 2024-12-29 |
| **Status** | Draft |
| **Author** | Fork Maintainer |

---

## 1. Overview

### 1.1 Problem Statement

The current MCP Atlassian implementation lacks:

1. **Confluence Analytics**: No ability to retrieve page view counts, viewer information, or engagement metrics. Users cannot answer questions like "Which pages are most popular?" or "Is anyone reading my documentation?"

2. **Jira SLA Metrics**: While date fields and changelog data exist, they are not exposed in a user-friendly way for workflow analysis. Users cannot easily answer "How long do issues spend in each status?" or "Are we meeting our SLA targets?"

### 1.2 Goals

1. Enable AI agents to analyze Confluence page engagement and usage patterns
2. Enable AI agents to calculate and report on Jira workflow SLAs
3. Provide flexible, user-configurable tools that give control over returned data
4. Support batch operations for efficiency in analysis workflows
5. Maintain consistency with existing MCP Atlassian patterns and conventions

### 1.3 Non-Goals

- Building a full analytics dashboard (this provides data for AI analysis)
- Real-time streaming of analytics data
- Historical data beyond what Atlassian APIs provide
- Custom SLA rule engines (calculated metrics are predefined, raw data allows custom analysis)

---

## 2. User Stories

### Confluence Analytics

1. **As a documentation owner**, I want to see how many people view my pages so I can prioritize maintenance efforts.

2. **As a team lead**, I want to identify stale documentation that no one reads so I can archive or update it.

3. **As a knowledge manager**, I want to understand which topics are trending so I can create more relevant content.

4. **As an AI agent**, I want raw view data with configurable fields so I can perform custom analysis without unnecessary context.

### Jira SLA Metrics

1. **As a project manager**, I want to know the average time issues spend in each status so I can identify bottlenecks.

2. **As a team lead**, I want to track whether issues are resolved before their due dates so I can report on SLA compliance.

3. **As an analyst**, I want raw timestamp data so I can calculate custom metrics specific to my workflow.

4. **As an AI agent**, I want configurable metric selection so I can minimize response size and focus on relevant data.

---

## 3. Detailed Specifications

## 3.1 Jira Tools

### 3.1.1 `jira_get_issue_dates` (Raw Data)

**Purpose**: Retrieve raw date and timeline data for workflow analysis.

#### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `issue_keys` | `string \| list[string]` | Yes | - | Single issue key (e.g., "PROJ-123") or list for batch operations |
| `include_created` | `boolean` | No | `true` | Include issue creation timestamp |
| `include_updated` | `boolean` | No | `true` | Include last updated timestamp |
| `include_due_date` | `boolean` | No | `true` | Include due date |
| `include_resolution_date` | `boolean` | No | `true` | Include resolution timestamp |
| `include_status_changes` | `boolean` | No | `true` | Include status transition history from changelog |
| `status_change_detail` | `string` | No | `"both"` | One of: `"summary"`, `"detailed"`, `"both"` |

#### Status Change Detail Levels

- **`summary`**: Aggregated time per status (e.g., "In Progress": "5d 2h 30m")
- **`detailed`**: Full transition log with enter/exit timestamps
- **`both`**: Include both summary and detailed data

#### Response Schema

```json
{
  "issues": {
    "<issue_key>": {
      "issue_key": "string",
      "created": "ISO-8601 timestamp | null",
      "updated": "ISO-8601 timestamp | null",
      "due_date": "YYYY-MM-DD | null",
      "resolution_date": "ISO-8601 timestamp | null",
      "current_status": "string",
      "status_changes": {
        "summary": {
          "<status_name>": {
            "total_time_minutes": "integer",
            "formatted": "string (e.g., '5d 2h 30m')"
          }
        },
        "detailed": [
          {
            "status": "string",
            "entered_at": "ISO-8601 timestamp",
            "exited_at": "ISO-8601 timestamp | null (if current)",
            "duration_minutes": "integer",
            "transitioned_by": "string (display name)"
          }
        ]
      }
    }
  },
  "metadata": {
    "requested_at": "ISO-8601 timestamp",
    "issue_count": "integer",
    "includes": ["created", "updated", "..."]
  }
}
```

#### Duration Units

All duration values are returned in **minutes** as the base unit. A formatted string representation is also provided for human readability.

| Raw Field | Type | Description |
|-----------|------|-------------|
| `total_time_minutes` | integer | Duration in minutes |
| `duration_minutes` | integer | Duration in minutes |
| `formatted` | string | Human-readable format: `Xd Xh Xm` |

**Formatting Rules:**
- Days = 24 hours (calendar time by default)
- Hours = 60 minutes
- Format omits zero values (e.g., "2h 30m" not "0d 2h 30m")

---

### 3.1.2 `jira_get_issue_sla` (Calculated Metrics)

**Purpose**: Calculate SLA and workflow metrics from issue data.

#### Environment Configuration

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `JIRA_SLA_METRICS` | `string` | `"cycle_time,time_in_status"` | Comma-separated list of default metrics |
| `JIRA_SLA_WORKING_HOURS_ONLY` | `boolean` | `false` | Exclude non-working hours from calculations |
| `JIRA_SLA_WORKING_HOURS_START` | `string` | `"09:00"` | Start of working day (24h format, local time) |
| `JIRA_SLA_WORKING_HOURS_END` | `string` | `"17:00"` | End of working day (24h format, local time) |
| `JIRA_SLA_WORKING_DAYS` | `string` | `"1,2,3,4,5"` | Working days (1=Monday, 7=Sunday) |
| `JIRA_SLA_TIMEZONE` | `string` | `"UTC"` | Timezone for working hours calculation |

#### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `issue_keys` | `string \| list[string]` | Yes | - | Single issue key or list for batch |
| `metrics` | `list[string]` | No | from config | Override default metrics to calculate |
| `working_hours_only` | `boolean` | No | from config | Override working hours setting |
| `include_raw_dates` | `boolean` | No | `false` | Include raw timestamps alongside metrics |

#### Available Metrics

| Metric ID | Description | Calculation |
|-----------|-------------|-------------|
| `cycle_time` | Time from creation to resolution | `resolution_date - created` |
| `lead_time` | Time from creation to current/closed | `now_or_resolution - created` |
| `time_in_status` | Duration in each status | Aggregated from changelog |
| `time_to_first_transition` | Time until first status change | `first_transition - created` |
| `due_date_compliance` | Whether resolved before due date | Compare `resolution_date` vs `due_date` |
| `resolution_time` | Time from first "In Progress" to resolution | `resolution_date - first_in_progress` |
| `response_time` | Time to first comment or transition | `min(first_comment, first_transition) - created` |

#### Response Schema

```json
{
  "issues": {
    "<issue_key>": {
      "issue_key": "string",
      "metrics": {
        "cycle_time": {
          "value_minutes": "integer",
          "formatted": "string",
          "calculated": "boolean (false if issue not resolved)"
        },
        "time_in_status": {
          "<status_name>": {
            "value_minutes": "integer",
            "formatted": "string",
            "percentage": "float (% of total time)"
          }
        },
        "due_date_compliance": {
          "status": "met | missed | no_due_date | not_resolved",
          "margin_minutes": "integer (positive = early, negative = late)",
          "formatted_margin": "string"
        }
      },
      "raw_dates": {
        "created": "ISO-8601 | null",
        "resolution_date": "ISO-8601 | null",
        "due_date": "YYYY-MM-DD | null"
      }
    }
  },
  "metadata": {
    "requested_at": "ISO-8601 timestamp",
    "issue_count": "integer",
    "metrics_calculated": ["cycle_time", "..."],
    "working_hours_applied": "boolean",
    "working_hours_config": {
      "start": "09:00",
      "end": "17:00",
      "days": [1, 2, 3, 4, 5],
      "timezone": "UTC"
    }
  }
}
```

#### Working Hours Calculation

When `working_hours_only=true`:

1. **Working Days**: Only days specified in `JIRA_SLA_WORKING_DAYS` are counted
   - Format: Comma-separated integers (1=Monday, 7=Sunday)
   - Default: `1,2,3,4,5` (Monday-Friday)

2. **Working Hours**: Only hours within the specified range are counted
   - Format: 24-hour time strings
   - Default: `09:00` to `17:00`

3. **Timezone**: All calculations use the specified timezone
   - Default: `UTC`
   - Accepts: IANA timezone names (e.g., `America/New_York`, `Europe/London`)

4. **Example**:
   - Issue created: Friday 4:00 PM
   - Issue resolved: Monday 10:00 AM
   - Calendar time: ~66 hours
   - Working hours only: 1h (Fri) + 1h (Mon) = 2 hours

---

## 3.2 Confluence Tools

### 3.2.1 `confluence_get_page_views` (Raw View Data)

**Purpose**: Retrieve raw view and engagement data for pages.

**Note**: Requires Confluence Cloud. Analytics API is not available on Server/Data Center.

#### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `page_ids` | `string \| list[string]` | Yes | - | Single page ID or list for batch |
| `from_date` | `string` | No | `null` | Start date (ISO-8601), null = all time |
| `to_date` | `string` | No | `null` | End date (ISO-8601), null = now |
| `include_total_views` | `boolean` | No | `true` | Include total view count |
| `include_unique_viewers` | `boolean` | No | `true` | Include unique viewer count |
| `include_viewer_list` | `boolean` | No | `false` | Include list of viewers |
| `include_view_trend` | `boolean` | No | `false` | Include daily/weekly breakdown |
| `trend_granularity` | `string` | No | `"daily"` | One of: `"daily"`, `"weekly"` |
| `viewer_limit` | `integer` | No | `10` | Max viewers to return (1-100) |

#### Response Schema

```json
{
  "pages": {
    "<page_id>": {
      "page_id": "string",
      "page_title": "string",
      "space_key": "string",
      "total_views": "integer | null",
      "unique_viewers": "integer | null",
      "last_viewed_at": "ISO-8601 timestamp | null",
      "viewers": [
        {
          "user_id": "string",
          "display_name": "string",
          "email": "string | null",
          "view_count": "integer",
          "last_viewed_at": "ISO-8601 timestamp"
        }
      ],
      "view_trend": [
        {
          "period": "YYYY-MM-DD | YYYY-Www",
          "views": "integer",
          "unique_viewers": "integer"
        }
      ]
    }
  },
  "metadata": {
    "requested_at": "ISO-8601 timestamp",
    "page_count": "integer",
    "date_range": {
      "from": "ISO-8601 | null",
      "to": "ISO-8601"
    },
    "includes": ["total_views", "unique_viewers", "..."]
  }
}
```

---

### 3.2.2 `confluence_get_page_analytics` (Calculated Metrics)

**Purpose**: Calculate engagement and usage metrics for pages.

#### Environment Configuration

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `CONFLUENCE_ANALYTICS_METRICS` | `string` | `"engagement_score,staleness"` | Default metrics to calculate |
| `CONFLUENCE_ANALYTICS_PERIOD_DAYS` | `integer` | `30` | Default analysis period |

#### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `page_ids` | `string \| list[string]` | Yes | - | Single page ID or list for batch |
| `metrics` | `list[string]` | No | from config | Override metrics to calculate |
| `period_days` | `integer` | No | from config | Analysis period in days |
| `include_raw_data` | `boolean` | No | `false` | Include raw view counts alongside metrics |

#### Available Metrics

| Metric ID | Description | Calculation |
|-----------|-------------|-------------|
| `engagement_score` | Composite engagement rating (0-100) | Weighted: views (40%) + unique viewers (30%) + recency (30%) |
| `view_velocity` | Trend in view activity | Compare current vs previous period |
| `staleness` | Content freshness indicator | Days since last view and edit |
| `viewer_diversity` | Breadth of audience | unique_viewers / total_views ratio |
| `peak_activity` | When page is most viewed | Aggregate by day-of-week and hour |
| `repeat_viewer_rate` | Audience retention | viewers_with_multiple_visits / unique_viewers |

#### Response Schema

```json
{
  "pages": {
    "<page_id>": {
      "page_id": "string",
      "page_title": "string",
      "period_days": "integer",
      "metrics": {
        "engagement_score": {
          "value": "integer (0-100)",
          "components": {
            "view_score": "integer",
            "viewer_score": "integer",
            "recency_score": "integer"
          }
        },
        "view_velocity": {
          "trend": "increasing | decreasing | stable",
          "current_period_views": "integer",
          "previous_period_views": "integer",
          "change_percent": "float"
        },
        "staleness": {
          "days_since_last_view": "integer",
          "days_since_last_edit": "integer",
          "status": "active | stale | abandoned",
          "stale_threshold_days": "integer"
        },
        "viewer_diversity": {
          "ratio": "float (0-1)",
          "interpretation": "narrow | moderate | broad"
        }
      },
      "raw_data": {
        "total_views": "integer",
        "unique_viewers": "integer",
        "last_viewed_at": "ISO-8601",
        "last_edited_at": "ISO-8601"
      }
    }
  },
  "metadata": {
    "requested_at": "ISO-8601 timestamp",
    "page_count": "integer",
    "period_days": "integer",
    "metrics_calculated": ["engagement_score", "..."]
  }
}
```

#### Engagement Score Calculation

The engagement score (0-100) is calculated as:

```
engagement_score = (view_score * 0.4) + (viewer_score * 0.3) + (recency_score * 0.3)

view_score = min(100, (total_views / expected_views) * 100)
  where expected_views = period_days * 2 (adjustable baseline)

viewer_score = min(100, (unique_viewers / expected_viewers) * 100)
  where expected_viewers = period_days * 0.5

recency_score = max(0, 100 - (days_since_last_view * 5))
  decays 5 points per day without views
```

#### Staleness Status

| Status | Criteria |
|--------|----------|
| `active` | Viewed within last 7 days |
| `stale` | Not viewed in 7-90 days |
| `abandoned` | Not viewed in 90+ days |

---

### 3.2.3 `confluence_get_space_analytics` (Space-Level Insights)

**Purpose**: Get aggregated analytics across an entire space.

#### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `space_key` | `string` | Yes | - | Space key to analyze |
| `include_popular_pages` | `boolean` | No | `true` | Top pages by views |
| `include_stale_pages` | `boolean` | No | `false` | Pages with low/no views |
| `include_trending_pages` | `boolean` | No | `false` | Pages with increasing views |
| `include_space_summary` | `boolean` | No | `true` | Aggregated space metrics |
| `period_days` | `integer` | No | `30` | Analysis period |
| `limit` | `integer` | No | `10` | Max pages per category (1-50) |
| `stale_threshold_days` | `integer` | No | `90` | Days without views to be "stale" |

#### Response Schema

```json
{
  "space_key": "string",
  "space_name": "string",
  "period_days": "integer",
  "summary": {
    "total_pages": "integer",
    "total_views": "integer",
    "unique_viewers": "integer",
    "avg_views_per_page": "float",
    "median_views_per_page": "float",
    "pages_with_zero_views": "integer",
    "stale_page_count": "integer",
    "most_active_day": "string (day name)",
    "engagement_score": "integer (0-100, space average)"
  },
  "popular_pages": [
    {
      "page_id": "string",
      "title": "string",
      "views": "integer",
      "unique_viewers": "integer",
      "url": "string"
    }
  ],
  "trending_pages": [
    {
      "page_id": "string",
      "title": "string",
      "views": "integer",
      "growth_percent": "float",
      "url": "string"
    }
  ],
  "stale_pages": [
    {
      "page_id": "string",
      "title": "string",
      "last_viewed_at": "ISO-8601 | null",
      "last_edited_at": "ISO-8601",
      "days_stale": "integer",
      "url": "string"
    }
  ],
  "metadata": {
    "requested_at": "ISO-8601 timestamp",
    "includes": ["popular_pages", "space_summary", "..."]
  }
}
```

---

## 4. API Dependencies

### 4.1 Jira APIs Used

| Endpoint | Purpose | Cloud | Server/DC |
|----------|---------|-------|-----------|
| `GET /rest/api/3/issue/{key}` | Issue with dates | Yes | Yes |
| `POST /rest/api/3/issue/{key}?expand=changelog` | Issue with changelog | Yes | Yes |
| `POST /rest/api/3/changelog/bulkfetch` | Batch changelogs | Yes | No |

### 4.2 Confluence APIs Used

| Endpoint | Purpose | Cloud | Server/DC |
|----------|---------|-------|-----------|
| `GET /wiki/rest/api/analytics/content/{id}/views` | Page views | Yes | No |
| `GET /wiki/rest/api/analytics/content/{id}/viewers` | Viewer list | Yes | No |
| `GET /wiki/rest/api/analytics/space/{key}/views` | Space views | Yes | No |

**Important**: Confluence analytics features require **Cloud only**. Server/Data Center does not expose analytics APIs.

---

## 5. Configuration Summary

### 5.1 New Environment Variables

#### Jira SLA

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `JIRA_SLA_METRICS` | string | `cycle_time,time_in_status` | Default SLA metrics |
| `JIRA_SLA_WORKING_HOURS_ONLY` | boolean | `false` | Use working hours only |
| `JIRA_SLA_WORKING_HOURS_START` | string | `09:00` | Working day start |
| `JIRA_SLA_WORKING_HOURS_END` | string | `17:00` | Working day end |
| `JIRA_SLA_WORKING_DAYS` | string | `1,2,3,4,5` | Working days (1=Mon) |
| `JIRA_SLA_TIMEZONE` | string | `UTC` | Timezone for calculations |

#### Confluence Analytics

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `CONFLUENCE_ANALYTICS_METRICS` | string | `engagement_score,staleness` | Default metrics |
| `CONFLUENCE_ANALYTICS_PERIOD_DAYS` | integer | `30` | Default analysis period |

---

## 6. Error Handling

### 6.1 Error Responses

All tools return errors in a consistent format:

```json
{
  "error": {
    "code": "string",
    "message": "string",
    "details": {}
  }
}
```

### 6.2 Error Codes

| Code | Description |
|------|-------------|
| `INVALID_ISSUE_KEY` | Issue key format invalid or issue not found |
| `INVALID_PAGE_ID` | Page ID not found |
| `CHANGELOG_NOT_AVAILABLE` | Changelog endpoint not available (Server/DC batch) |
| `ANALYTICS_NOT_AVAILABLE` | Analytics API not available (Confluence Server/DC) |
| `INVALID_DATE_RANGE` | from_date > to_date or invalid format |
| `RATE_LIMITED` | API rate limit exceeded |
| `PERMISSION_DENIED` | User lacks permission to view resource |

---

## 7. Success Metrics

1. **Adoption**: Tools are used in >50% of analytics-related queries
2. **Performance**: Batch operations complete in <5s for 50 issues/pages
3. **Accuracy**: SLA calculations match manual verification in 99% of cases
4. **User Satisfaction**: Configurable parameters reduce unnecessary API calls by 40%

---

## 8. Future Considerations

1. **Custom SLA Rules**: Allow users to define custom SLA formulas
2. **Caching**: Cache analytics data to reduce API calls
3. **Webhooks**: Real-time SLA breach notifications
4. **Export**: Generate SLA reports in CSV/PDF format
5. **Server/DC Analytics**: Investigate alternative approaches for on-premise analytics
