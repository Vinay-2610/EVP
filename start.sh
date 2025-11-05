#!/bin/bash
cd ev_route_planner_backend/backend
python -m uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}
