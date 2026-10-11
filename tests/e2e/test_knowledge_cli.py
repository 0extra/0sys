from __future__ import annotations

import pytest
from typer.testing import CliRunner

from zerosys.cli.app import app

pytestmark = pytest.mark.e2e


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


def test_explain_term_lists_glossary(runner: CliRunner) -> None:
    result = runner.invoke(app, ["explain-term", "--list"])

    assert result.exit_code == 0
    assert "Glossary" in result.stdout
    assert "ufw" in result.stdout


def test_explain_term_without_argument_lists(runner: CliRunner) -> None:
    result = runner.invoke(app, ["explain-term"])

    assert result.exit_code == 0
    assert "ufw" in result.stdout


def test_explain_term_known(runner: CliRunner) -> None:
    result = runner.invoke(app, ["explain-term", "firewall"])

    assert result.exit_code == 0
    assert "Firewall" in result.stdout


def test_explain_term_unknown(runner: CliRunner) -> None:
    result = runner.invoke(app, ["explain-term", "nonsense-term-xyz"])

    assert result.exit_code == 1


def test_tips_lists_categories(runner: CliRunner) -> None:
    result = runner.invoke(app, ["tips"])

    assert result.exit_code == 0
    assert "firewall" in result.stdout


def test_tips_known_category(runner: CliRunner) -> None:
    result = runner.invoke(app, ["tips", "ssh"])

    assert result.exit_code == 0
    assert "ssh" in result.stdout.lower()


def test_tips_unknown_category(runner: CliRunner) -> None:
    result = runner.invoke(app, ["tips", "nonsense-category-xyz"])

    assert result.exit_code == 1
