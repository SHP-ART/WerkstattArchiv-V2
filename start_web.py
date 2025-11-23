#!/usr/bin/env python3
"""Schnellstart-Script für Web-UI mit Debugging"""

import sys
import time

print("=== Web-App Start ===")
print("Step 1: Import logging...")
start = time.time()
import logging
print(f"✓ logging in {time.time()-start:.2f}s")

print("Step 2: Import json, threading...")
start = time.time()
import json
import threading
print(f"✓ json, threading in {time.time()-start:.2f}s")

print("Step 3: Import pathlib, datetime...")
start = time.time()
from pathlib import Path
from datetime import datetime
from queue import Queue, Empty
print(f"✓ pathlib, datetime in {time.time()-start:.2f}s")

print("Step 4: Import Flask...")
start = time.time()
from flask import Flask, render_template, request, jsonify, send_file
print(f"✓ Flask in {time.time()-start:.2f}s")

print("Step 5: Import config...")
start = time.time()
import config
print(f"✓ config in {time.time()-start:.2f}s")

print("Step 6: Import db...")
start = time.time()
import db
print(f"✓ db in {time.time()-start:.2f}s")

print("Step 7: Import parser...")
start = time.time()
import parser as auftrag_parser
print(f"✓ parser in {time.time()-start:.2f}s")

print("Step 8: Import ocr...")
start = time.time()
import ocr
print(f"✓ ocr in {time.time()-start:.2f}s")

print("Step 9: Import archive...")
start = time.time()
import archive
print(f"✓ archive in {time.time()-start:.2f}s")

print("Step 10: Import watcher...")
start = time.time()
import watcher
print(f"✓ watcher in {time.time()-start:.2f}s")

print("\n=== Alle Imports erfolgreich! ===\n")

# Jetzt starte web_app
print("Starting web app...")
import web_app
