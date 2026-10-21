# Jira Issue & Defect Tracking Integration

IntelliIncident integrates with **Jira Cloud** (via Jira REST API v3) to provide issue tracking, defect records, and change ticket telemetry as the fourth real evidence source. Jira evidence correlates alongside **GitHub** code intelligence, **Sentry** runtime error intelligence, and **Prometheus** metric telemetry to produce explainable, multi-dimensional Root Cause Analysis (RCA).

---

## 1. Architectural Overview

```
                      ┌────────────────────────────────────────┐
                      │          Atlassian Jira Cloud          │
                      │    (e.g., https://org.atlassian.net)   │
                      └──────────────────┬─────────────────────┘
                                         │ Jira REST API v3 (Basic Auth: Email + API Token)
                                         ▼
┌────────────────────────────────────────────────────────────────────────┐
│                   IntelliIncident Backend                              │
│                                                                        │
│   ┌────────────────────────────────────────────────────────────────┐   │
│   │                      JiraService                               │   │
│   │  • Health & Reachability checks (`/rest/api/3/myself`)         │   │
│   │  • Parameterized JQL query execution (`/rest/api/3/search/jql`)│   │
│   │  • Single issue retrieval (`/rest/api/3/issue/{issue_key}`)    │   │
│   │  • ADF (Atlassian Document Format) rich text extraction        │   │
│   │  • Deterministic correlation scoring (0.0 to 1.0)              │   │
│   └────────────────────────────────┬───────────────────────────────┘   │
│                                    │ JiraEvidence                      │
│                                    ▼                                   │
│   ┌────────────────────────────────────────────────────────────────┐   │
│   │                    EvidenceCorrelator                          │   │
│   │  • DEPLOYMENT: Release & change management ticket correlation  │   │
│   │  • DATABASE: Database maintenance & query defect correlation   │   │
│   │  • INFRASTRUCTURE: Capacity, node, & resource issue correlation│   │
│   │  • CODE_ERROR: Bug reports & regression ticket correlation     │   │
│   │  • TRAFFIC & NETWORK: Load & connectivity defect correlation   │   │
│   │  • Quad-Source Correlation: GitHub + Sentry + Prometheus + Jira│   │
│   └────────────────────────────────┬───────────────────────────────┘   │
│                                    │ Root Cause Candidates             │
│                                    ▼                                   │
│                        FastAPI REST API Routes                         │
│             (/api/jira/health, /issues, /evidence/{incident_id})       │
└────────────────────────────────────┬───────────────────────────────────┘
                                     │ JSON API
                                     ▼
┌────────────────────────────────────────────────────────────────────────┐
│                   IntelliIncident React Dashboard                      │
│                                                                        │
│   • `JiraEvidenceCard.tsx` in Incident Details & Investigation         │
│   • Jira Ticket Key, Type, Status, Priority, Assignee badges           │
│   • Correlation score (0-100%) and matched factor badges               │
│   • Live external link to Jira Cloud issues                            │
│   • Seamless degradation when Jira is unconfigured or offline          │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Configuration

Jira connectivity is configured via environment variables and loaded into `backend/app/core/config.py`:

| Environment Variable | Default Value | Description |
|----------------------|---------------|-------------|
| `JIRA_BASE_URL`      | `None` (empty)| Base URL of the Jira instance (e.g., `https://your-domain.atlassian.net`) |
| `JIRA_EMAIL`         | `None` (empty)| Jira account email address used for Basic Authentication |
| `JIRA_API_TOKEN`     | `None` (empty)| Jira API token generated from Atlassian Account Settings |
| `JIRA_PROJECT_KEY`   | `None` (empty)| Default Jira project key (e.g., `PROJ`, `INC`, `DEV`) |

### Example Configuration (`backend/.env`)
```bash
# Jira Issue Tracking Integration
JIRA_BASE_URL=https://my-company.atlassian.net
JIRA_EMAIL=devops@my-company.com
JIRA_API_TOKEN=your_jira_api_token_here
JIRA_PROJECT_KEY=OPS
```

### Graceful Degradation & Unconfigured Mode
If any of `JIRA_BASE_URL`, `JIRA_EMAIL`, or `JIRA_API_TOKEN` are omitted:
- IntelliIncident continues operating without errors or crashes.
- Endpoints return `configured: false`, `reachable: false`, and `status: "UNCONFIGURED"`.
- Root cause analysis gracefully proceeds using the remaining telemetry sources (GitHub, Sentry, Prometheus, logs, metrics).
- Zero fake, simulated, or hardcoded Jira tickets are ever injected into production responses.

---

## 3. Endpoints

The Jira integration exposes four FastAPI endpoints registered under `/api`:

### 1. `GET /api/jira/health`
Checks Jira configuration and reachability.
- **200 OK Response (Configured & Reachable):**
  ```json
  {
    "configured": true,
    "reachable": true,
    "base_url": "https://my-company.atlassian.net",
    "project_key": "OPS",
    "authenticated_user": "devops@my-company.com",
    "status": "HEALTHY",
    "message": "Connected to Jira Cloud as devops@my-company.com"
  }
  ```
- **200 OK Response (Unconfigured):**
  ```json
  {
    "configured": false,
    "reachable": false,
    "base_url": null,
    "project_key": null,
    "authenticated_user": null,
    "status": "UNCONFIGURED",
    "message": "Jira is not configured. Set JIRA_BASE_URL, JIRA_EMAIL, and JIRA_API_TOKEN."
  }
  ```

### 2. `GET /api/jira/issues?jql={query}&limit=20`
Searches Jira issues using Jira Query Language (JQL) or retrieves the latest project issues.
- Query Parameters:
  - `jql` (optional): Jira Query Language string. Defaults to `ORDER BY created DESC`.
  - `limit` (optional): Maximum tickets returned (default 20, max 100).

### 3. `GET /api/jira/issues/{issue_key}`
Retrieves a specific Jira issue by its key (e.g., `OPS-101`). Returns 404 if not found.

### 4. `GET /api/jira/evidence/{incident_id}`
Retrieves Jira evidence correlated specifically with an existing incident.
- Looks up incident metadata (service, environment, title, timestamp).
- Queries Jira issues created or updated around the incident.
- Runs the deterministic correlation algorithm and returns sorted matching issues.

---

## 4. Deterministic Correlation Algorithm

Rather than simple string matching, `JiraService.calculate_correlation()` computes an explainable correlation score between an incident and each candidate Jira issue:

```
Correlation Score = min(1.0, Sum of Matched Factor Weights * Status Multiplier)
```

### Factor Weights:
| Factor | Weight | Condition |
|--------|--------|-----------|
| **Exact Key / ID Match** | `+1.00` | Incident ID appears in issue key, summary, or description |
| **Service Match** | `+0.40` | Incident service name matches Jira component or issue text |
| **Failure Mode Match** | `+0.30` | Failure keywords (`timeout`, `oom`, `exception`, `latency`, `deadlock`, `deploy`) match issue |
| **Environment Match** | `+0.20` | Incident environment (`production`, `staging`) appears in issue labels or text |
| **Title Token Match** | `+0.20` | Significant title keywords (>3 chars) overlap between incident and issue |

### Status Multipliers:
- **In Progress / Open / In Review / Investigating / Reopened:** `1.0x` (Active issues)
- **Closed / Resolved / Done:** `0.8x` (Resolved issues, useful for recent change analysis)

### Threshold:
Tickets with a correlation score `≥ 0.35` are retained as correlated evidence. The specific matched factors are preserved in `matched_factors` for full explainability.

---

## 5. Atlassian Document Format (ADF) Handling

Jira Cloud REST API v3 returns issue descriptions structured as hierarchical JSON documents following the Atlassian Document Format (ADF), rather than plain text or markdown.

`JiraService._extract_adf_text()` recursively traverses the ADF tree:
- Extracts `text` from `type: "text"` nodes.
- Extracts `title` from inline and block card links.
- Handles legacy plain strings from Jira Server/DC or v2 APIs transparently.

---

## 6. Root Cause Analysis (RCA) Integration

Jira evidence is fed directly into `EvidenceCorrelator.correlate()`, contributing to root cause hypotheses across all major failure categories:

1. **DEPLOYMENT**:
   - Matches deployment, release, migration, or hotfix tickets.
   - Increases DEPLOYMENT root cause score by `+0.15`.
   - Adds evidence citations referencing Jira ticket key, summary, and status.

2. **DATABASE**:
   - Matches database migration, schema alteration, or connection pool tickets.
   - Increases DATABASE root cause score by `+0.15`.

3. **INFRASTRUCTURE**:
   - Matches node scaling, maintenance, disk, or memory resource tickets.
   - Increases INFRASTRUCTURE root cause score by `+0.15`.

4. **CODE_ERROR**:
   - Matches regression, exception, or software bug tickets.
   - Increases CODE_ERROR root cause score by `+0.15`.

5. **TRAFFIC & NETWORK**:
   - Matches traffic spikes, DDoS, DNS, or network maintenance tickets.
   - Increases respective category scores by `+0.15`.

### Quad-Source Cross-Correlation
When all four telemetry sources confirm a post-deployment failure:
1. **GitHub**: Recent commit modifying application source code.
2. **Sentry**: High-frequency runtime exception triggered after deployment.
3. **Prometheus**: Latency, CPU, or error rate deviation spiking simultaneously.
4. **Jira**: Correlated release ticket or open deployment incident ticket.

When all four sources align:
- DEPLOYMENT category confidence is boosted by `+0.25` (capped at 0.98).
- A unified quad-source finding is generated citing the commit SHA, Sentry error, metric deviation percentage, and Jira issue key.

---

## 7. Frontend Integration

1. **`src/components/Incident/JiraEvidenceCard.tsx`**:
   - Renders Jira status badge (Connected vs Unconfigured vs Offline).
   - Displays issue key, issue type, status badge, priority, and assignee.
   - Displays correlation score progress bar and colored badges for matched factors.
   - Provides external link button to open the issue in Jira Cloud.
   - Displays transparent empty state with clear configuration guidance when no tickets correlate or Jira is unconfigured.

2. **`src/pages/IncidentDetailsPage.tsx`**:
   - Displays `JiraEvidenceCard` alongside GitHub Commits, Sentry Runtime Evidence, and Prometheus Metric Telemetry in the Evidence section.

3. **`src/pages/InvestigationPage.tsx`**:
   - Replaces static ticket placeholder in the "Support Tickets" telemetry section with live Jira telemetry.
