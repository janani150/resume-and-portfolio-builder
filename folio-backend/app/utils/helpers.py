"""Small helper utilities used across the app."""
from datetime import datetime


def now_iso():
    """Return current UTC time as ISO string."""
    return datetime.utcnow().isoformat() + "Z"
