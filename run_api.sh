#!/bin/bash
# Startup script for the API server

cd "$(dirname "$0")"
python api/server.py

