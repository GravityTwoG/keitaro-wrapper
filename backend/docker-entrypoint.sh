#!/bin/sh
set -eu

alembic upgrade head
exec uvicorn keitaro_wrapper.main:app --host 0.0.0.0 --port 8000
