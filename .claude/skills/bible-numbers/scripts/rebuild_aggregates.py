#!/usr/bin/env python3
"""Regenerate data/all-numbers.json, data/all-numbers.min.json and all_numbers.js from the number files."""
import numlib as L

if __name__ == "__main__":
    nums = L.rebuild_aggregates()
    print(f"rebuilt data/all-numbers*.json and all_numbers.js: {len(nums)} numbers")
