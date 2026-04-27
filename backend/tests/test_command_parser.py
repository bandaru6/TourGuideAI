import pytest

from app.engine.command_parser import CommandType, parse_command


def test_skip_command():
    """'Skip this stop' should parse as SKIP_STOP."""
    result = parse_command("skip this stop")
    assert result.type == CommandType.SKIP_STOP
    assert result.confidence > 0.5


def test_food_command():
    """'Find food nearby' should parse as FIND_FOOD."""
    result = parse_command("I'm hungry, find food nearby")
    assert result.type == CommandType.FIND_FOOD
    assert result.confidence > 0.5


def test_eta_command():
    """'When will we arrive' should parse as ETA_DESTINATION."""
    result = parse_command("when will we arrive at the destination")
    assert result.type == CommandType.ETA_DESTINATION
    assert result.confidence > 0.5


def test_unknown_command():
    """Random text should parse as UNKNOWN with low confidence."""
    result = parse_command("the weather is nice today")
    assert result.type == CommandType.UNKNOWN
    assert result.confidence == 0.0


def test_partial_match_confidence():
    """Partial keyword matches should have lower confidence than full matches."""
    full = parse_command("skip this stop please")
    partial = parse_command("skip")
    assert full.confidence >= partial.confidence


def test_case_insensitive():
    """Command parsing should be case insensitive."""
    upper = parse_command("SKIP THIS STOP")
    lower = parse_command("skip this stop")
    assert upper.type == lower.type
    assert upper.confidence == lower.confidence
