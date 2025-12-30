# Implementation Plan: Analytics & SLA Metrics

## Overview

This document outlines the implementation plan for adding Confluence analytics and Jira SLA metrics to MCP Atlassian. Refer to `prd-analytics-sla.md` for detailed specifications.

---

## Branch Strategy

### Branch Naming Convention

```
feature/<phase>-<short-description>
```

### Branch Structure

```
main (protected - no direct commits)
│
├── feature/phase1-jira-dates
│   └── PR → main (after Phase 1 complete)
│
├── feature/phase2-jira-sla
│   └── PR → main (after Phase 2 complete)
│
├── feature/phase3-confluence-views
│   └── PR → main (after Phase 3 complete)
│
├── feature/phase4-confluence-analytics
│   └── PR → main (after Phase 4 complete)
│
├── feature/phase5-space-analytics
│   └── PR → main (after Phase 5 complete)
│
└── feature/phase6-docs-tests
    └── PR → main (after Phase 6 complete)
```

### Branch Workflow

1. **Create feature branch from main**
   ```bash
   git checkout main
   git pull origin main
   git checkout -b feature/phase1-jira-dates
   ```

2. **Make commits on feature branch**
   ```bash
   git add .
   git commit -m "feat(jira): add metrics models for issue dates"
   ```

3. **Keep branch updated with main**
   ```bash
   git fetch origin
   git rebase origin/main
   ```

4. **Create PR when phase is complete**
   ```bash
   git push origin feature/phase1-jira-dates
   # Create PR via GitHub
   ```

5. **After PR merge, clean up**
   ```bash
   git checkout main
   git pull origin main
   git branch -d feature/phase1-jira-dates
   ```

### Commit Message Convention

Follow conventional commits:

```
feat(jira): add issue dates tool
feat(confluence): add page views analytics
fix(jira): handle null resolution date
docs: update README with new tools
test(jira): add SLA calculation tests
refactor(confluence): extract analytics mixin
```

### PR Requirements

Before merging a PR:
- [ ] All tests pass
- [ ] Linting passes (`ruff check`)
- [ ] Type checking passes (`mypy`)
- [ ] PR description includes summary of changes
- [ ] At least one review (if team project)

---

## Phase Summary

| Phase | Branch | Scope | Estimated Files Changed | Status |
|-------|--------|-------|------------------------|--------|
| 1 | `feature/phase1-jira-dates` | Jira Raw Dates Tool | 8 files | ✅ Completed |
| 2 | `feature/phase2-jira-sla` | Jira SLA Metrics Tool | 6 files | ✅ Completed |
| 3 | `feature/phase3-confluence-views` | Confluence Page Views Tool | 8 files | ✅ Completed |
| 4 | `feature/phase4-confluence-analytics` | Confluence Analytics Tool | 4 files | ✅ Completed |
| 5 | `feature/phase5-space-analytics` | Confluence Space Analytics Tool | 3 files | ✅ Completed |
| 6 | `feature/phase6-docs-tests` | Documentation & Testing | 5 files | 🔲 Pending |

### Completed Tools

**Phase 1 - `jira_get_issue_dates`**: Raw date and timeline extraction from Jira issues
- Extracts created, updated, due_date, resolution_date
- Parses changelog for status transition history
- Supports batch operations and configurable field selection

**Phase 2 - `jira_get_issue_sla`**: SLA metrics calculation
- Metrics: cycle_time, lead_time, time_in_status, due_date_compliance, resolution_time, first_response_time
- Working hours filtering (exclude weekends/non-business hours)
- Environment-based configuration with per-request overrides
- Returns raw status changes for custom analysis

---

## Phase 1: Jira Raw Dates Tool (`jira_get_issue_dates`)

**Branch**: `feature/phase1-jira-dates`

### 1.1 Goals
- Expose raw date fields (created, updated, due_date, resolution_date)
- Parse and return status change history from changelog
- Support batch operations
- Configurable field selection

### 1.2 Files to Create/Modify

#### New Files

| File | Purpose |
|------|---------|
| `src/mcp_atlassian/jira/metrics.py` | New mixin for metrics/dates operations |
| `src/mcp_atlassian/models/jira/metrics.py` | Pydantic models for metrics responses |

#### Modified Files

| File | Changes |
|------|---------|
| `src/mcp_atlassian/jira/client.py` | Add `MetricsMixin` to `JiraFetcher` |
| `src/mcp_atlassian/jira/__init__.py` | Export new classes |
| `src/mcp_atlassian/models/jira/__init__.py` | Export new models |
| `src/mcp_atlassian/servers/jira.py` | Add `jira_get_issue_dates` tool |

### 1.3 Implementation Steps

```
1.3.1 Create feature branch
  □ git checkout -b feature/phase1-jira-dates

1.3.2 Create models (models/jira/metrics.py)
  □ StatusChangeEntry - single status transition
  □ StatusChangeSummary - aggregated time per status
  □ IssueDatesResponse - full response for single issue
  □ IssueDatesBatchResponse - batch response wrapper
  □ Commit: "feat(jira): add metrics models for issue dates"

1.3.3 Create metrics mixin (jira/metrics.py)
  □ get_issue_dates(issue_key, **options) -> IssueDatesResponse
  □ batch_get_issue_dates(issue_keys, **options) -> IssueDatesBatchResponse
  □ _parse_changelog_to_status_changes(changelog) -> list[StatusChangeEntry]
  □ _aggregate_status_times(changes) -> StatusChangeSummary
  □ _format_duration(minutes) -> str
  □ Commit: "feat(jira): add metrics mixin for date retrieval"

1.3.4 Integrate mixin into JiraFetcher
  □ Add MetricsMixin to JiraFetcher inheritance
  □ Commit: "feat(jira): integrate metrics mixin into fetcher"

1.3.5 Add MCP tool (servers/jira.py)
  □ Define jira_get_issue_dates tool with all parameters
  □ Wire to fetcher methods
  □ Handle single vs batch input
  □ Commit: "feat(jira): add jira_get_issue_dates MCP tool"

1.3.6 Write tests
  □ Unit tests for duration formatting
  □ Unit tests for changelog parsing
  □ Integration tests for tool
  □ Commit: "test(jira): add tests for issue dates tool"

1.3.7 Create PR
  □ Push branch to origin
  □ Create PR with description
  □ Run CI checks
  □ Merge to main
```

### 1.4 Key Implementation Details

#### Changelog Parsing Logic

```python
def _parse_changelog_to_status_changes(self, issue_key: str, changelogs: list[JiraChangelog]) -> list[StatusChangeEntry]:
    """
    Parse changelog to extract status transitions.

    Algorithm:
    1. Filter changelog items where field == "status"
    2. Sort by timestamp ascending
    3. For each status change, record:
       - status name (to_string)
       - entered_at (changelog.created)
       - exited_at (next changelog.created or None if current)
       - transitioned_by (changelog.author)
    4. Calculate duration_minutes for each entry
    """
```

#### Duration Formatting

```python
def _format_duration(self, minutes: int) -> str:
    """
    Format minutes into human-readable string.

    Examples:
    - 90 -> "1h 30m"
    - 1500 -> "1d 1h 0m"
    - 0 -> "0m"

    Rules:
    - 1 day = 24 hours (calendar time)
    - 1 hour = 60 minutes
    - Always show minutes
    - Omit days/hours if zero (except "0m")
    """
```

---

## Phase 2: Jira SLA Metrics Tool (`jira_get_issue_sla`)

**Branch**: `feature/phase2-jira-sla`

### 2.1 Goals
- Calculate SLA metrics from raw data
- Support working hours filtering
- Configurable via environment variables
- Per-call parameter overrides

### 2.2 Files to Create/Modify

#### New Files

| File | Purpose |
|------|---------|
| `src/mcp_atlassian/jira/sla.py` | SLA calculation logic |
| `src/mcp_atlassian/models/jira/sla.py` | SLA response models |

#### Modified Files

| File | Changes |
|------|---------|
| `src/mcp_atlassian/jira/config.py` | Add SLA config options |
| `src/mcp_atlassian/jira/client.py` | Add `SLAMixin` to `JiraFetcher` |
| `src/mcp_atlassian/servers/jira.py` | Add `jira_get_issue_sla` tool |
| `.env.example` | Document new SLA env vars |

### 2.3 Implementation Steps

```
2.3.1 Create feature branch
  □ git checkout main && git pull
  □ git checkout -b feature/phase2-jira-sla

2.3.2 Add SLA config (jira/config.py)
  □ JIRA_SLA_METRICS - default metrics list
  □ JIRA_SLA_WORKING_HOURS_ONLY - boolean
  □ JIRA_SLA_WORKING_HOURS_START - time string
  □ JIRA_SLA_WORKING_HOURS_END - time string
  □ JIRA_SLA_WORKING_DAYS - comma-separated ints
  □ JIRA_SLA_TIMEZONE - IANA timezone
  □ Commit: "feat(jira): add SLA configuration options"

2.3.3 Create SLA models (models/jira/sla.py)
  □ CycleTimeMetric
  □ TimeInStatusMetric
  □ DueDateComplianceMetric
  □ IssueSLAResponse
  □ IssueSLABatchResponse
  □ Commit: "feat(jira): add SLA metric models"

2.3.4 Create SLA mixin (jira/sla.py)
  □ get_issue_sla(issue_key, metrics, working_hours_only) -> IssueSLAResponse
  □ batch_get_issue_sla(issue_keys, ...) -> IssueSLABatchResponse
  □ _calculate_cycle_time(issue) -> CycleTimeMetric
  □ _calculate_time_in_status(issue) -> TimeInStatusMetric
  □ _calculate_due_date_compliance(issue) -> DueDateComplianceMetric
  □ _filter_working_hours(start, end) -> int (working minutes)
  □ Commit: "feat(jira): add SLA calculation mixin"

2.3.5 Implement working hours calculation
  □ Parse timezone config
  □ Filter out non-working days
  □ Filter out non-working hours
  □ Handle edge cases (spans multiple days/weeks)
  □ Commit: "feat(jira): implement working hours filter"

2.3.6 Add MCP tool (servers/jira.py)
  □ Define jira_get_issue_sla tool
  □ Load defaults from config
  □ Allow parameter overrides
  □ Commit: "feat(jira): add jira_get_issue_sla MCP tool"

2.3.7 Update .env.example
  □ Document all new SLA env vars
  □ Commit: "docs: add SLA config to .env.example"

2.3.8 Write tests
  □ Unit tests for each metric calculation
  □ Unit tests for working hours filtering
  □ Integration tests with mock data
  □ Commit: "test(jira): add SLA calculation tests"

2.3.9 Create PR
  □ Push branch, create PR, merge
```

### 2.4 Key Implementation Details

#### Working Hours Filter

```python
def _filter_working_hours(
    self,
    start_time: datetime,
    end_time: datetime,
    config: SLAConfig
) -> int:
    """
    Calculate working minutes between two timestamps.

    Algorithm:
    1. Convert times to configured timezone
    2. Iterate day by day from start to end
    3. For each day:
       a. Skip if not in working_days
       b. Calculate overlap with working hours
       c. Add to total
    4. Return total working minutes

    Edge cases:
    - start and end on same day
    - start/end outside working hours
    - spans weekends
    - spans multiple weeks
    """
```

#### Metric Calculator Registry

```python
METRIC_CALCULATORS = {
    "cycle_time": _calculate_cycle_time,
    "lead_time": _calculate_lead_time,
    "time_in_status": _calculate_time_in_status,
    "time_to_first_transition": _calculate_time_to_first_transition,
    "due_date_compliance": _calculate_due_date_compliance,
    "resolution_time": _calculate_resolution_time,
    "response_time": _calculate_response_time,
}
```

---

## Phase 3: Confluence Page Views Tool (`confluence_get_page_views`)

**Branch**: `feature/phase3-confluence-views`

### 3.1 Goals
- Fetch raw view data from Confluence Analytics API
- Support date range filtering
- Configurable field selection
- Batch operations

### 3.2 Files to Create/Modify

#### New Files

| File | Purpose |
|------|---------|
| `src/mcp_atlassian/confluence/analytics.py` | Analytics mixin |
| `src/mcp_atlassian/models/confluence/analytics.py` | Analytics models |

#### Modified Files

| File | Changes |
|------|---------|
| `src/mcp_atlassian/confluence/client.py` | Add `AnalyticsMixin` |
| `src/mcp_atlassian/confluence/v2_adapter.py` | Add analytics API calls |
| `src/mcp_atlassian/confluence/__init__.py` | Export new classes |
| `src/mcp_atlassian/models/confluence/__init__.py` | Export new models |
| `src/mcp_atlassian/servers/confluence.py` | Add tool |

### 3.3 Implementation Steps

```
3.3.1 Create feature branch
  □ git checkout main && git pull
  □ git checkout -b feature/phase3-confluence-views

3.3.2 Research Confluence Analytics API
  □ Verify endpoint paths for Cloud
  □ Test authentication requirements
  □ Document rate limits
  □ Identify response schemas
  □ Commit: "docs: document Confluence Analytics API research"

3.3.3 Add analytics to v2_adapter.py
  □ get_page_views(page_id, from_date, to_date) -> dict
  □ get_page_viewers(page_id, limit) -> list[dict]
  □ get_page_view_trend(page_id, granularity) -> list[dict]
  □ Handle Cloud-only restriction with clear error
  □ Commit: "feat(confluence): add analytics API calls to v2 adapter"

3.3.4 Create analytics models (models/confluence/analytics.py)
  □ PageViewer - single viewer info
  □ ViewTrendEntry - single period data
  □ PageViewsResponse - full response
  □ PageViewsBatchResponse - batch wrapper
  □ Commit: "feat(confluence): add analytics models"

3.3.5 Create analytics mixin (confluence/analytics.py)
  □ get_page_views(page_id, **options) -> PageViewsResponse
  □ batch_get_page_views(page_ids, **options) -> PageViewsBatchResponse
  □ Commit: "feat(confluence): add analytics mixin"

3.3.6 Add MCP tool (servers/confluence.py)
  □ Define confluence_get_page_views tool
  □ Handle Cloud-only with graceful error
  □ Commit: "feat(confluence): add confluence_get_page_views MCP tool"

3.3.7 Write tests
  □ Unit tests for model parsing
  □ Integration tests with mocked API
  □ Commit: "test(confluence): add page views tests"

3.3.8 Create PR
  □ Push branch, create PR, merge
```

### 3.4 Key Implementation Details

#### Cloud-Only Check

```python
def get_page_views(self, page_id: str, **options) -> PageViewsResponse:
    if not self.config.is_cloud:
        raise AnalyticsNotAvailableError(
            "Confluence Analytics API is only available on Cloud. "
            "Server/Data Center deployments do not support this feature."
        )
    # ... implementation
```

#### API Endpoint Reference

```
# Page view count
GET /wiki/rest/api/analytics/content/{contentId}/views
Query params: fromDate, toDate

# Page viewers
GET /wiki/rest/api/analytics/content/{contentId}/viewers
Query params: fromDate, toDate, limit

# View trend (if available)
GET /wiki/rest/api/analytics/content/{contentId}/views/trend
Query params: fromDate, toDate, granularity
```

---

## Phase 4: Confluence Page Analytics Tool (`confluence_get_page_analytics`)

**Branch**: `feature/phase4-confluence-analytics`

### 4.1 Goals
- Calculate engagement metrics from view data
- Support configurable metrics
- Environment variable defaults

### 4.2 Files to Modify

| File | Changes |
|------|---------|
| `src/mcp_atlassian/confluence/analytics.py` | Add metric calculations |
| `src/mcp_atlassian/confluence/config.py` | Add analytics config |
| `src/mcp_atlassian/models/confluence/analytics.py` | Add metric models |
| `src/mcp_atlassian/servers/confluence.py` | Add tool |

### 4.3 Implementation Steps

```
4.3.1 Create feature branch
  □ git checkout main && git pull
  □ git checkout -b feature/phase4-confluence-analytics

4.3.2 Add analytics config (confluence/config.py)
  □ CONFLUENCE_ANALYTICS_METRICS
  □ CONFLUENCE_ANALYTICS_PERIOD_DAYS
  □ Commit: "feat(confluence): add analytics configuration"

4.3.3 Create metric models
  □ EngagementScoreMetric
  □ ViewVelocityMetric
  □ StalenessMetric
  □ ViewerDiversityMetric
  □ PageAnalyticsResponse
  □ Commit: "feat(confluence): add analytics metric models"

4.3.4 Implement metric calculators
  □ _calculate_engagement_score(views, viewers, recency)
  □ _calculate_view_velocity(current_views, previous_views)
  □ _calculate_staleness(last_view, last_edit)
  □ _calculate_viewer_diversity(total_views, unique_viewers)
  □ Commit: "feat(confluence): implement metric calculators"

4.3.5 Add get_page_analytics method
  □ Fetch raw view data
  □ Calculate requested metrics
  □ Return structured response
  □ Commit: "feat(confluence): add get_page_analytics method"

4.3.6 Add MCP tool
  □ Define confluence_get_page_analytics
  □ Load defaults from config
  □ Commit: "feat(confluence): add confluence_get_page_analytics MCP tool"

4.3.7 Write tests
  □ Unit tests for each metric calculation
  □ Edge case handling
  □ Commit: "test(confluence): add analytics metric tests"

4.3.8 Create PR
  □ Push branch, create PR, merge
```

### 4.4 Metric Calculation Details

#### Engagement Score

```python
def _calculate_engagement_score(
    self,
    total_views: int,
    unique_viewers: int,
    days_since_last_view: int,
    period_days: int
) -> EngagementScoreMetric:
    """
    Calculate engagement score (0-100).

    Components:
    - view_score (40%): views vs expected baseline
    - viewer_score (30%): unique viewers vs expected
    - recency_score (30%): decays with time since last view

    Baselines:
    - expected_views = period_days * 2
    - expected_viewers = period_days * 0.5
    - recency decays 5 points per day without views
    """
    expected_views = period_days * 2
    expected_viewers = period_days * 0.5

    view_score = min(100, (total_views / expected_views) * 100)
    viewer_score = min(100, (unique_viewers / expected_viewers) * 100)
    recency_score = max(0, 100 - (days_since_last_view * 5))

    engagement = (view_score * 0.4) + (viewer_score * 0.3) + (recency_score * 0.3)

    return EngagementScoreMetric(
        value=int(engagement),
        components={
            "view_score": int(view_score),
            "viewer_score": int(viewer_score),
            "recency_score": int(recency_score)
        }
    )
```

---

## Phase 5: Confluence Space Analytics Tool (`confluence_get_space_analytics`)

**Branch**: `feature/phase5-space-analytics`

### 5.1 Goals
- Aggregate analytics across a space
- Identify popular, trending, and stale pages
- Provide space-level summary

### 5.2 Files to Modify

| File | Changes |
|------|---------|
| `src/mcp_atlassian/confluence/analytics.py` | Add space methods |
| `src/mcp_atlassian/models/confluence/analytics.py` | Add space models |
| `src/mcp_atlassian/servers/confluence.py` | Add tool |

### 5.3 Implementation Steps

```
5.3.1 Create feature branch
  □ git checkout main && git pull
  □ git checkout -b feature/phase5-space-analytics

5.3.2 Create space analytics models
  □ SpaceSummary
  □ PopularPage
  □ TrendingPage
  □ StalePage
  □ SpaceAnalyticsResponse
  □ Commit: "feat(confluence): add space analytics models"

5.3.3 Implement space analytics methods
  □ get_space_analytics(space_key, **options) -> SpaceAnalyticsResponse
  □ _get_space_pages(space_key) -> list[str] (page IDs)
  □ _calculate_space_summary(page_analytics) -> SpaceSummary
  □ _identify_popular_pages(page_analytics, limit) -> list[PopularPage]
  □ _identify_trending_pages(page_analytics, limit) -> list[TrendingPage]
  □ _identify_stale_pages(page_analytics, threshold, limit) -> list[StalePage]
  □ Commit: "feat(confluence): implement space analytics methods"

5.3.4 Add MCP tool
  □ Define confluence_get_space_analytics
  □ Support all optional parameters
  □ Commit: "feat(confluence): add confluence_get_space_analytics MCP tool"

5.3.5 Write tests
  □ Unit tests for page categorization
  □ Integration tests
  □ Commit: "test(confluence): add space analytics tests"

5.3.6 Create PR
  □ Push branch, create PR, merge
```

### 5.4 Implementation Notes

#### Performance Consideration

```python
def get_space_analytics(self, space_key: str, **options) -> SpaceAnalyticsResponse:
    """
    NOTE: This may make multiple API calls for spaces with many pages.

    Optimization strategies:
    1. Use space-level analytics endpoint if available
    2. Batch page analytics requests
    3. Cache results for configured period
    4. Limit pages analyzed (e.g., top 100 by recent edit)
    """
```

---

## Phase 6: Documentation & Testing

**Branch**: `feature/phase6-docs-tests`

### 6.1 Documentation Updates

| File | Updates |
|------|---------|
| `README.md` | Add new tools to tool reference |
| `.env.example` | Document all new env vars |
| `AGENTS.md` | Update with new patterns |

### 6.2 Test Files to Create

| File | Purpose |
|------|---------|
| `tests/unit/jira/test_metrics.py` | Unit tests for Jira metrics |
| `tests/unit/jira/test_sla.py` | Unit tests for SLA calculations |
| `tests/unit/confluence/test_analytics.py` | Unit tests for Confluence analytics |
| `tests/integration/test_jira_metrics_tools.py` | Integration tests |
| `tests/integration/test_confluence_analytics_tools.py` | Integration tests |

### 6.3 Implementation Steps

```
6.3.1 Create feature branch
  □ git checkout main && git pull
  □ git checkout -b feature/phase6-docs-tests

6.3.2 Update README.md
  □ Add new Jira tools to tool reference
  □ Add new Confluence tools to tool reference
  □ Add configuration section for SLA/Analytics
  □ Commit: "docs: add new tools to README"

6.3.3 Update .env.example
  □ Add all Jira SLA env vars with descriptions
  □ Add all Confluence analytics env vars
  □ Commit: "docs: update .env.example with new config options"

6.3.4 Update AGENTS.md
  □ Document new patterns for metrics/analytics
  □ Commit: "docs: update AGENTS.md with new patterns"

6.3.5 Add comprehensive integration tests
  □ End-to-end tests for Jira metrics tools
  □ End-to-end tests for Confluence analytics tools
  □ Commit: "test: add integration tests for new tools"

6.3.6 Final review
  □ Run full test suite
  □ Run linting and type checking
  □ Manual testing of all new tools
  □ Commit any fixes

6.3.7 Create PR
  □ Push branch, create PR, merge
```

### 6.4 Test Scenarios

#### Jira Metrics Tests

```
□ Duration formatting (various inputs)
□ Changelog parsing with multiple status changes
□ Changelog with no status changes
□ Issue with missing dates (null handling)
□ Batch operation with mixed results
□ Working hours filter (same day)
□ Working hours filter (spans weekend)
□ Working hours filter (spans multiple weeks)
□ Cycle time calculation (resolved vs unresolved)
□ Due date compliance (met, missed, no due date)
```

#### Confluence Analytics Tests

```
□ Page with views
□ Page with zero views
□ Viewer list parsing
□ View trend aggregation
□ Engagement score boundaries (0, 100, middle)
□ Staleness categorization (active, stale, abandoned)
□ Space summary aggregation
□ Popular pages sorting
□ Trending pages growth calculation
□ Cloud-only error handling
```

---

## Dependency Graph

```
Phase 1 (Jira Dates) ──────► PR → main
    │
    └──► Phase 2 (Jira SLA) ──────► PR → main
              │
              │   (depends on Phase 1 for raw data methods)

Phase 3 (Confluence Views) ──────► PR → main
    │
    ├──► Phase 4 (Confluence Analytics) ──────► PR → main
    │         │
    │         │   (depends on Phase 3 for view data)
    │
    └──► Phase 5 (Space Analytics) ──────► PR → main
              │
              │   (depends on Phase 3 and 4)

Phase 6 (Docs & Tests) ──────► PR → main
    │
    │   (can start after Phase 1, continues throughout)
```

---

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| Confluence Analytics API unavailable/changed | High | Research API first, fail gracefully |
| Working hours calculation complexity | Medium | Comprehensive unit tests, use established library |
| Performance with large batches | Medium | Implement pagination, consider caching |
| Changelog API differences Cloud vs Server | Medium | Test both, document limitations |
| Rate limiting on batch operations | Low | Implement backoff, respect limits |
| Merge conflicts between phases | Low | Keep PRs focused, merge promptly |

---

## Checklist

### Pre-Implementation
- [ ] Review PRD with stakeholder
- [ ] Research Confluence Analytics API availability
- [ ] Set up test environment with sample data
- [ ] Review existing codebase patterns

### Phase 1 (`feature/phase1-jira-dates`) ✅ COMPLETED
- [x] Create branch from main
- [x] Create models/jira/metrics.py
- [x] Create jira/metrics.py mixin
- [x] Integrate into JiraFetcher
- [x] Add MCP tool
- [x] Write unit tests
- [x] Manual testing
- [x] Create PR and merge
- **PR**: https://github.com/meliezer124/mcp-atlassian-analyzer/pull/1

### Phase 2 (`feature/phase2-jira-sla`) ✅ COMPLETED
- [x] Create branch from main (after Phase 1 merged)
- [x] Add SLA config options
- [x] Create models/jira/sla.py
- [x] Create jira/sla.py mixin
- [x] Implement working hours filter
- [x] Add MCP tool
- [x] Write unit tests
- [x] Manual testing
- [x] Create PR and merge
- **PR**: https://github.com/meliezer124/mcp-atlassian-analyzer/pull/2

### Phase 3 (`feature/phase3-confluence-views`) ✅ COMPLETED
- [x] Create branch from main
- [x] Research Confluence Analytics API
- [x] Add analytics to v2_adapter.py
- [x] Create models/confluence/analytics.py
- [x] Create confluence/analytics.py mixin
- [x] Add MCP tool
- [x] Write unit tests
- [x] Manual testing
- [x] Create PR and merge
- **PR**: https://github.com/meliezer124/mcp-atlassian-analyzer/pull/4

### Phase 4 (`feature/phase4-confluence-analytics`)
- [ ] Create branch from main (after Phase 3 merged)
- [ ] Add analytics config
- [ ] Create metric models
- [ ] Implement metric calculators
- [ ] Add MCP tool
- [ ] Write unit tests
- [ ] Manual testing
- [ ] Create PR and merge

### Phase 5 (`feature/phase5-space-analytics`)
- [ ] Create branch from main (after Phase 4 merged)
- [ ] Create space models
- [ ] Implement space analytics
- [ ] Add MCP tool
- [ ] Write unit tests
- [ ] Manual testing
- [ ] Create PR and merge

### Phase 6 (`feature/phase6-docs-tests`)
- [ ] Create branch from main (after all phases merged)
- [ ] Update README.md
- [ ] Update .env.example
- [ ] Update AGENTS.md
- [ ] Write integration tests
- [ ] Final review and cleanup
- [ ] Create PR and merge
