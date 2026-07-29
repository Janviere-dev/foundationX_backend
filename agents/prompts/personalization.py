#!/usr/bin/env python3

from typing import List, Optional


def format_first_name(first_name: Optional[str]) -> str:
    return first_name or "the student"


def format_goals(goals: Optional[List[str]]) -> str:
    if not goals:
        return "No specific goals set - teach generally to the curriculum."
    return ", ".join(goals)
