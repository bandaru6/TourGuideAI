"""
Deterministic voice command parser.

Matches transcript text against keyword patterns to identify commands.
No LLM required — uses simple keyword matching with confidence scoring.
"""

import re
from enum import Enum

from pydantic import BaseModel


class CommandType(str, Enum):
    SKIP_STOP = "skip_stop"
    FIND_FOOD = "find_food"
    FIND_GAS = "find_gas"
    DISTANCE_NEXT = "distance_next"
    ETA_DESTINATION = "eta_destination"
    PAUSE_NARRATION = "pause_narration"
    RESUME_NARRATION = "resume_narration"
    UNKNOWN = "unknown"


class ParsedCommand(BaseModel):
    type: CommandType
    confidence: float
    params: dict = {}


class VoiceCommandRequest(BaseModel):
    transcript: str
    lat: float | None = None
    lng: float | None = None


# Pattern → (CommandType, confidence)
# Each pattern is a list of keyword groups; matching more groups gives higher confidence
COMMAND_PATTERNS: dict[CommandType, list[list[str]]] = {
    CommandType.SKIP_STOP: [
        ["skip", "stop"],
        ["skip", "this"],
        ["next", "stop"],
        ["pass", "stop"],
        ["skip"],
    ],
    CommandType.FIND_FOOD: [
        ["find", "food"],
        ["find", "restaurant"],
        ["hungry"],
        ["eat", "near"],
        ["food", "near"],
        ["restaurant"],
        ["find", "eat"],
    ],
    CommandType.FIND_GAS: [
        ["find", "gas"],
        ["gas", "station"],
        ["need", "gas"],
        ["fuel"],
        ["find", "fuel"],
        ["charging", "station"],
        ["need", "charge"],
    ],
    CommandType.DISTANCE_NEXT: [
        ["how", "far", "next"],
        ["distance", "next"],
        ["how", "far"],
        ["next", "stop", "far"],
    ],
    CommandType.ETA_DESTINATION: [
        ["eta", "destination"],
        ["when", "arrive"],
        ["how", "long", "left"],
        ["time", "remaining"],
        ["eta"],
        ["when", "get", "there"],
    ],
    CommandType.PAUSE_NARRATION: [
        ["stop", "talking"],
        ["mute"],
        ["quiet"],
        ["pause", "narration"],
        ["silence"],
        ["shut", "up"],
    ],
    CommandType.RESUME_NARRATION: [
        ["start", "talking"],
        ["unmute"],
        ["resume", "narration"],
        ["speak"],
        ["talk", "again"],
    ],
}


def parse_command(transcript: str) -> ParsedCommand:
    """
    Parse a voice transcript into a command using deterministic keyword matching.

    Returns the best matching command with confidence score.
    Higher confidence = more keyword groups matched.
    """
    if not transcript or not transcript.strip():
        return ParsedCommand(type=CommandType.UNKNOWN, confidence=0.0)

    words = set(re.findall(r"\w+", transcript.lower()))
    best_type = CommandType.UNKNOWN
    best_confidence = 0.0

    for cmd_type, patterns in COMMAND_PATTERNS.items():
        for i, keyword_group in enumerate(patterns):
            if all(kw in words for kw in keyword_group):
                # Earlier patterns in the list are more specific → higher confidence
                confidence = 1.0 - (i * 0.1)
                # Bonus for matching more keywords
                confidence = min(1.0, confidence + len(keyword_group) * 0.05)
                if confidence > best_confidence:
                    best_confidence = confidence
                    best_type = cmd_type
                break  # Only take the best pattern per command type

    # Clamp confidence
    best_confidence = round(min(1.0, max(0.0, best_confidence)), 2)

    return ParsedCommand(type=best_type, confidence=best_confidence)
