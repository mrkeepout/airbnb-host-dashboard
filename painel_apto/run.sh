#!/bin/sh
# O SUPERVISOR_TOKEN é injetado automaticamente pelo Home Assistant OS
cd /opt
exec python -m uvicorn app.main:app --host 0.0.0.0 --port 8234
