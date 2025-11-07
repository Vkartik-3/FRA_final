#!/bin/bash
#
# FRA Dashboard Launcher
#
# This script launches the FRA Streamlit dashboard
# Usage: ./run_dashboard.sh
#

# Change to script directory
cd "$(dirname "$0")"

# Activate virtual environment
source env/bin/activate

# Launch dashboard
echo "🚀 Launching FRA Dashboard..."
echo "📊 Dashboard will open in your browser at http://localhost:8501"
echo ""
echo "Press Ctrl+C to stop the dashboard"
echo ""

streamlit run scripts/dashboard_fra.py
