#!/usr/bin/env bash
echo "Cloning projects from $1 into $2"
if [ -z "$3" ]; then
    python clone_projects.py --from=$1 --to=$2
else
    python clone_projects.py --from=$1 --to=$2 --symlink=$3
fi
