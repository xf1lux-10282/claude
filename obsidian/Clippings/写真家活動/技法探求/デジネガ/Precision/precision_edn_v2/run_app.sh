#!/bin/bash
# Precision EDN v2 - Streamlit起動スクリプト

cd "$(dirname "$0")"

echo "=========================================="
echo "  Precision EDN v2 - Streamlit GUI"
echo "=========================================="
echo ""
echo "起動中..."
echo ""

streamlit run app.py
