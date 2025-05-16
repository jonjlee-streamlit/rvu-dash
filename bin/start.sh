#!/bin/bash

INTERACTIVE=false

# Parse options
while getopts "i" opt; do
  case $opt in
    i)
      INTERACTIVE=true
      ;;
    \?)
      echo "Invalid option: -$OPTARG" >&2
      exit 1
      ;;
  esac
done

if [ "$INTERACTIVE" = true ]; then
    # Interactive mode
    pipenv run streamlit run app.py
else
    # Background mode
    nohup pipenv run streamlit run app.py &> nohup.out & echo $! > streamlit.pid
    echo "Dashboard started in background. PID saved to streamlit.pid"
fi