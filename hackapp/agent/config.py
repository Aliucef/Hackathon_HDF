"""
Agent Configuration
Settings for the desktop agent
"""

import os
from typing import Dict

# Middleware connection
MIDDLEWARE_URL = os.getenv("MIDDLEWARE_URL", "http://localhost:5000")
MIDDLEWARE_TOKEN = os.getenv("MIDDLEWARE_TOKEN", "hackathon_demo_token")

# Hotkey mappings
HOTKEYS: Dict[str, str] = {
    '<ctrl>+<alt>+v': 'CTRL+ALT+V',  # Voice AI summarization
    '<ctrl>+<alt>+d': 'CTRL+ALT+D',  # Drug interaction checker
}

# UI Automation settings
AUTO_INSERT_ENABLED = True
INSERT_DELAY_MS = 10  # Delay between characters when typing (milliseconds)
INSERT_PAUSE_BEFORE = 0.5  # Pause before starting insertion (seconds)
INSERT_PAUSE_AFTER = 0.2  # Pause after insertion (seconds)

# DXCare simulation
DXCARE_WINDOW_KEYWORDS = ['DXCare', 'dxcare', 'Patient Chart', 'Epic']  # Keywords to identify DXCare window

# Context capture
BACKUP_CLIPBOARD = True  # Whether to backup and restore clipboard after capturing

# Agent behavior
SHOW_NOTIFICATIONS = True  # Show visual notifications
VERBOSE_LOGGING = True  # Print detailed logs to console

# Timeout settings
REQUEST_TIMEOUT_SECONDS = 30  # Timeout for middleware requests

# User identification (optional)
USER_ID = os.getenv("USER_ID", "demo_clinician")
