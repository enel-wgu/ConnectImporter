from __future__ import annotations

from typing import Iterable

from connect_config.models.common import ValidationIssue


def format_summary(config, issues: Iterable[ValidationIssue]) -> str:
    counts = config.counts()
    warnings = sum(1 for issue in issues if issue.severity == "WARNING")
    errors = sum(1 for issue in issues if issue.severity == "ERROR")
    lines = [
        "Export complete",
        "",
        f"Queues:              {counts['Queues']}",
        f"Routing profiles:    {counts['Routing profiles']}",
        f"Security profiles:   {counts['Security profiles']}",
        f"Users:               {counts['Users']}",
        f"Hierarchy groups:    {counts['Hierarchy groups']}",
        f"Hours:                {counts['Hours']}",
        f"Contact flows:       {counts['Contact flows']}",
        f"Flow modules:          {counts['Flow modules']}",
        f"Prompts:               {counts['Prompts']}",
        f"Quick connects:        {counts['Quick connects']}",
        "",
        f"Warnings:              {warnings}",
        f"Errors:                 {errors}",
    ]
    return "\n".join(lines)
