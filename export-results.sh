#!/usr/bin/env bash
echo "Saving daily commit data"
python szzExportResults.py ./ user_project_date_totalcommits.csv user_language_date_totalcommits.csv
