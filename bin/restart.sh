#!/bin/bash
# Get existing PID from the file
OLD_PID=$(cat streamlit.pid 2>/dev/null)
[ -z "$OLD_PID" ] && { echo "No existing process found"; exit 1; }

# Kill process and verify
kill $OLD_PID || { echo "Existing process $OLD_PID could not be terminated"; exit 1; }

# Restart
nohup pipenv run streamlit run app.py &> nohup.out & echo $! > streamlit.pid
echo "Dashboard restarted. PID saved to streamlit.pid"