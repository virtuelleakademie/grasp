#!/bin/bash

if [ -n "$1" ]; then
  # If argument is provided, use it as EXERCISE_NAME
  EXERCISE_NAME="$1" chainlit run app.py --host 0.0.0.0 --port 10000
else
  # Otherwise run without the environment variable
  chainlit run app.py --host 0.0.0.0 --port 10000
fi