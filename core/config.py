import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
SERVICES_DIR = BASE_DIR / "services"
SHARED_DIR = BASE_DIR / "shared"

# Gateway Configuration
GATEWAY_PORT = int(os.getenv("OASIS_PORT", 5050))

# Platform Metadata
IS_WINDOWS = sys.platform.startswith("win")
IS_LINUX = sys.platform.startswith("linux")
IS_DARWIN = sys.platform.startswith("darwin")

APP_NAME = "Oasis Reconnaissance & Intelligence Suite"
APP_VERSION = "3.0.0"
ANALYST_NAME = "User"
ANALYST_ROLE = "INTELLIGENCE ANALYST"
