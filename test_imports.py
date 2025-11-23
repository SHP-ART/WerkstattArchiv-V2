#!/usr/bin/env python3
"""Test imports to find hanging module"""

import sys
print(f"Python version: {sys.version}")

print("Testing imports...")

try:
    print("1. Importing json...")
    import json
    print("   ✓ json OK")
except Exception as e:
    print(f"   ✗ json FAILED: {e}")
    sys.exit(1)

try:
    print("2. Importing pathlib...")
    from pathlib import Path
    print("   ✓ pathlib OK")
except Exception as e:
    print(f"   ✗ pathlib FAILED: {e}")
    sys.exit(1)

try:
    print("3. Importing yaml...")
    import yaml
    print("   ✓ yaml OK")
except Exception as e:
    print(f"   ✗ yaml FAILED: {e}")
    sys.exit(1)

try:
    print("4. Importing logging...")
    import logging
    print("   ✓ logging OK")
except Exception as e:
    print(f"   ✗ logging FAILED: {e}")
    sys.exit(1)

try:
    print("5. Importing flask...")
    import flask
    print("   ✓ flask OK")
except Exception as e:
    print(f"   ✗ flask FAILED: {e}")
    sys.exit(1)

try:
    print("6. Importing pytesseract...")
    import pytesseract
    print("   ✓ pytesseract OK")
except Exception as e:
    print(f"   ✗ pytesseract FAILED: {e}")
    sys.exit(1)

try:
    print("7. Importing pdf2image...")
    import pdf2image
    print("   ✓ pdf2image OK")
except Exception as e:
    print(f"   ✗ pdf2image FAILED: {e}")
    sys.exit(1)

try:
    print("8. Importing config module...")
    import config
    print("   ✓ config OK")
except Exception as e:
    print(f"   ✗ config FAILED: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\nAll imports successful!")
print("Creating Config instance...")
try:
    cfg = config.Config()
    print("✓ Config instance created successfully")
except Exception as e:
    print(f"✗ Config creation FAILED: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n=== ALL TESTS PASSED ===")
