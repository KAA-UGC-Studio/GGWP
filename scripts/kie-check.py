#!/usr/bin/env python3
"""
kie-check.py — verify the kie.ai connection.

Reads KIE_API_KEY (env or project-root .env), calls the credit endpoint, and
prints the balance. Run this after adding your key to confirm the integration
is live:

    python scripts/kie-check.py
"""

import sys
from pathlib import Path

# Windows consoles default to cp1252, which can't encode the status glyphs below.
try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _kie


def main() -> None:
    key = _kie.get_api_key()  # exits with guidance if missing
    masked = key[:4] + "…" + key[-4:] if len(key) > 8 else "(set)"
    print(f"KIE_API_KEY found: {masked}")
    credits = _kie.get_credit()
    print(f"✅ Connected to kie.ai — {credits} credits remaining.")
    if credits <= 0:
        print("   ⚠️  Balance is 0 — top up at https://kie.ai/pricing before generating.")


if __name__ == "__main__":
    main()
