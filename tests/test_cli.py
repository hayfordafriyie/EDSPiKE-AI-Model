import sys
from pathlib import Path

import pytest

from src.cli import build_parser, run_cli


class TestCLI:
    def test_build_parser_version(self):
        parser = build_parser()
        args = parser.parse_args(["--version"])
        assert args.version is True

    def test_build_parser_prompt(self):
        parser = build_parser()
        args = parser.parse_args(["fix the bug"])
        assert " ".join(args.prompt) == "fix the bug"

    def test_build_parser_model_flag(self):
        parser = build_parser()
        args = parser.parse_args(["-m", "gpt-4", "-p", "openai"])
        assert args.model == "gpt-4"
        assert args.provider == "openai"

    def test_build_parser_directory(self):
        parser = build_parser()
        args = parser.parse_args(["-d", "/tmp/test"])
        assert args.dir == "/tmp/test"

    def test_build_parser_quiet(self):
        parser = build_parser()
        args = parser.parse_args(["-q", "hello"])
        assert args.quiet is True

    def test_run_cli_version(self):
        rc = run_cli(["--version"])
        assert rc == 0
