"""Tests for the CLI module (basic usage only)."""

import sys
from pathlib import Path

import pytest

from src.cli import main, parse_args


def test_parse_args_output(monkeypatch):
    """Test that parse_args correctly parses the output argument."""
    monkeypatch.setattr(sys, "argv", ["cli.py", "--output", "report.html"])
    parsed_args = parse_args()
    assert parsed_args.output == Path("report.html")


def test_parse_args_help(monkeypatch, capsys):
    """Test that parse_args shows help and exits when called with --help."""
    monkeypatch.setattr(sys, "argv", ["cli.py", "--help"])
    with pytest.raises(SystemExit):
        parse_args()
    captured = capsys.readouterr()
    assert "Animal names collateral adjective scraper" in captured.out
    assert "--output" in captured.out
