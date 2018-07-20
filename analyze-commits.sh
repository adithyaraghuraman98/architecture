#!/usr/bin/env bash
echo "Starting the analysis of Git repos $1"
python szz.py --analyze --thread=16 --repos="$1"
