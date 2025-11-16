#!/bin/bash
# Startup script for the Streamlit dashboard

cd "$(dirname "$0")"
streamlit run dashboard/dashboard.py

