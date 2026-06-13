#!/bin/bash
export PATH="$HOME/.local/bin:$PATH"
cd /opt/wm2026
exec uvicorn app:app --host 0.0.0.0 --port 8000
