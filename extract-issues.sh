#!/usr/bin/env bash
echo "Extracting issues for projects listed in $1"
python szzExtractIssues.py --from=$1 --to=extracted-issues.csv