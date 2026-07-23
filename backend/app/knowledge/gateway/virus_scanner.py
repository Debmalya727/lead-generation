"""
Phase 14.1 Enterprise Knowledge Gateway — Security Virus Scanner.
Inspects incoming asset content for malicious scripts, executable signatures,
SQL injection vectors, and macro payloads.
"""
from __future__ import annotations

import logging
import re
from typing import Dict, Any, Tuple

logger = logging.getLogger("backend.knowledge.gateway.virus_scanner")

DISALLOWED_PATTERNS = [
    r"<script[\s\S]*?>[\s\S]*?eval\(",
    r"DROP\s+TABLE\s+",
    r"DELETE\s+FROM\s+\w+\s+WHERE\s+1=1",
    r"rm\s+-rf\s+/",
    r"powershell\.exe\s+-EncodedCommand",
    r"cmd\.exe\s+/c",
    r"\\x90\\x90\\x90\\x90",  # NOP sled
    r"AutoOpen\(\)|Workbook_Open\(\)", # Malicious VBA macros
]


class SecurityVirusScanner:
    """Security scanner for asset contents entering Knowledge Gateway."""

    def scan_content(self, title: str, content: str) -> Tuple[bool, Dict[str, Any]]:
        """Scans raw text or URI content for security threats."""
        threats_found = []

        for pattern in DISALLOWED_PATTERNS:
            if re.search(pattern, content, re.IGNORECASE):
                threats_found.append(pattern)

        is_safe = len(threats_found) == 0
        details = {
            "title": title,
            "content_size": len(content),
            "threats_count": len(threats_found),
            "detected_threats": threats_found,
        }

        if not is_safe:
            logger.warning(f"[VirusScanner] SECURITY ALERT: Asset '{title}' failed scan! Threats: {threats_found}")
        else:
            logger.debug(f"[VirusScanner] Asset '{title}' passed security virus scan.")

        return is_safe, details


virus_scanner = SecurityVirusScanner()
