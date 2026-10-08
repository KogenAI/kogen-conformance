#!/usr/bin/env python3
"""Mutation executable: usage-shaped output with invalid UTF-8."""
import os

os.write(1, b"kogen\xff\n")
raise SystemExit(2)
