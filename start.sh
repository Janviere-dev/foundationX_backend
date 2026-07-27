#!/usr/bin/env bash

python3 -m venv venv
source venv/bin/activate
pip install -r requiremnents.txt
uvicorn main:app --port 8000 --reload
