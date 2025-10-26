# Renovate Dependency Dashboard

## Overview

The Dependency Dashboard is an automated issue created and maintained by Renovate bot to provide visibility into pending dependency updates for the repository.

## What is the Dependency Dashboard?

The Dependency Dashboard (Issue) serves as a centralized location to:
- View all pending dependency updates
- Track which updates are awaiting their schedule
- Manually trigger updates before their scheduled time
- Monitor the overall dependency health of the project

## Understanding the Dashboard Sections

### Awaiting Schedule

This section lists dependency updates that are scheduled to run at specific times based on the `renovate.json` configuration. The current configuration uses:
- **Weekly schedule**: Updates are grouped and created once per week
- **Package-specific schedules**: 
  - pytest packages, linting tools, OpenTelemetry, Flask: Monday before 3am
  - Frontend dependencies: Tuesday before 3am

To trigger an update immediately, simply check the box next to the update in the issue.

### Detected Dependencies

This section would display all detected dependencies in the repository. It appears when:
- `:dependencyDashboardApproval` preset is enabled (requires manual approval for updates)
- Renovate first scans the repository
- There are specific dependency issues to highlight

**Note**: In this repository, this section is not populated because we use automatic scheduling and automerge for minor/patch updates.

## Current Renovate Configuration

Location: `renovate.json`

Key features:
- **Dependency Dashboard**: Enabled via `:dependencyDashboard` preset
- **Semantic Commits**: Uses conventional commit format
- **Grouped Updates**: Non-major updates are grouped together
- **Schedule**: Weekly updates (can be overridden per package type)
- **Automerge**: Enabled for minor and patch updates
- **Security Alerts**: Enabled for vulnerability detection

## Package Management

The repository uses multiple package managers:
- **Poetry**: Python dependencies (pyproject.toml)
- **pip**: Python requirements (requirements*.txt files)
- **npm**: JavaScript/TypeScript dependencies (package.json in web/ and workers/billing-api/)
- **GitHub Actions**: Workflow action versions

## How Updates Work

1. **Scheduled Scan**: Renovate scans the repository weekly
2. **Update Detection**: Identifies available updates based on version constraints
3. **PR Creation**: Creates pull requests for updates (respecting schedule and grouping rules)
4. **Automerge**: Automatically merges minor/patch updates that pass CI
5. **Manual Review**: Major updates require manual review and approval

## Dependency Groups

The configuration includes several package groups:
- **pytest packages**: All pytest-related dependencies
- **linting tools**: mypy, ruff, black
- **OpenTelemetry packages**: All opentelemetry-* packages
- **Flask packages**: Flask and Flask extensions
- **frontend dependencies**: All npm packages

## Triggering Updates Manually

To manually trigger an update before its scheduled time:
1. Navigate to the Dependency Dashboard issue
2. Find the update in the "Awaiting Schedule" section
3. Check the box next to the update
4. Renovate will create the PR within minutes

## No Action Required

⚠️ **Important**: The Dependency Dashboard issue itself is **not a bug or problem**. It's a feature that provides visibility into dependency management. 

The issue will:
- Update automatically as Renovate scans for updates
- Close and reopen as needed
- Always remain open to track pending updates

## Further Reading

- [Renovate Dependency Dashboard Documentation](https://docs.renovatebot.com/key-concepts/dashboard/)
- [Renovate Configuration Options](https://docs.renovatebot.com/configuration-options/)
- [Repository's renovate.json](../renovate.json)
