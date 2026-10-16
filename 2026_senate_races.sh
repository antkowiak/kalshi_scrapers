#!/bin/bash
while true
do
    data=$(python3 ./2026_senate_races.py)
    clear
    echo "$data"
    sleep 60
done

