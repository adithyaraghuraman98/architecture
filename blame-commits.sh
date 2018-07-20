#!/usr/bin/env bash
echo "Starting the blaming of mined commits"
python szz.py --blame --thread=16 --repos=$1
