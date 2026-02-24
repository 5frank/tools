#!/usr/bin/env python3
"""Example script: utils/timestamp"""
from datetime import datetime

def main():
    now = datetime.now()
    print(f"Current timestamp: {now.isoformat()}")

if __name__ == "__main__":
    main()
