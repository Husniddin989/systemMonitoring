#!/bin/bash

BOT_TOKEN="7120243579:AAEoaMz5DK8pv1uvwmbD--Mmt8nqbhL_mec"
CHAT_ID="664131109"

for i in {1..5}; do
    MESSAGE=$(ps -eo comm,%cpu --sort=-%cpu | awk '
        NR==1 {next}
        NR<=11 {
            sum += $2
            printf "│   - %-20s (%s%%)\n", $1, $2
        }
        END {
            printf "\nUmumiy CPU usage (TOP 10): %.1f%%\n", sum
        }
    ')
    
    curl -s -X POST "https://api.telegram.org/bot$BOT_TOKEN/sendMessage" \
        -d chat_id="$CHAT_ID" \
        --data-urlencode text="$MESSAGE"

    sleep 10
done