import sys
from pathlib import Path

# Vercel entrypoint: project modules use top-level imports (`from bot import ...`), so src/ must be on the path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from main import app  # noqa: E402,F401
