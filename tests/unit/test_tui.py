from __future__ import annotations

from pathlib import Path

import pytest
from textual.widgets import Button, Input

from zerosys.tui.app import ConfirmScreen, ZeroSysTUI, _default_state_path

pytestmark = pytest.mark.unit

TEST_SIZE = (120, 40)


@pytest.mark.asyncio
async def test_tui_app_compose() -> None:
    app = ZeroSysTUI()
    async with app.run_test(size=TEST_SIZE) as pilot:
        assert app.query_one("#btn-load", Button) is not None
        assert app.query_one("#btn-plan", Button) is not None
        assert app.query_one("#log") is not None
        await pilot.pause()


@pytest.mark.asyncio
async def test_tui_buttons_disabled_initially() -> None:
    app = ZeroSysTUI()
    async with app.run_test(size=TEST_SIZE) as pilot:
        assert app.query_one("#btn-plan", Button).disabled is True
        assert app.query_one("#btn-check", Button).disabled is True
        assert app.query_one("#btn-apply", Button).disabled is True
        await pilot.pause()


@pytest.mark.asyncio
async def test_tui_load_enables_buttons(tmp_path: Path) -> None:
    config_path = tmp_path / "0sys.yaml"
    config_path.write_text(
        "version: 1\nserver:\n  hostname: test\nfirewall:\n  default: deny\n  allow: [22]\n",
        encoding="utf-8",
    )

    app = ZeroSysTUI()
    async with app.run_test(size=TEST_SIZE) as pilot:
        input_widget = app.query_one("#config-path", Input)
        input_widget.value = str(config_path)
        await pilot.click("#btn-load")
        await pilot.pause()

        assert app.current_config is not None
        assert app.query_one("#btn-plan", Button).disabled is False
        assert app.query_one("#btn-check", Button).disabled is False
        assert app.query_one("#btn-apply", Button).disabled is False


@pytest.mark.asyncio
async def test_tui_apply_opens_confirmation_modal(tmp_path: Path) -> None:
    config_path = tmp_path / "0sys.yaml"
    config_path.write_text(
        "version: 1\nserver:\n  hostname: test\nfirewall:\n  default: deny\n  allow: [22]\n",
        encoding="utf-8",
    )

    app = ZeroSysTUI()
    async with app.run_test(size=TEST_SIZE) as pilot:
        input_widget = app.query_one("#config-path", Input)
        input_widget.value = str(config_path)
        await pilot.click("#btn-load")
        await pilot.pause()

        await pilot.click("#btn-apply")
        await pilot.pause()

        assert isinstance(app.screen, ConfirmScreen)


@pytest.mark.asyncio
async def test_tui_confirm_cancel_closes_modal(tmp_path: Path) -> None:
    config_path = tmp_path / "0sys.yaml"
    config_path.write_text(
        "version: 1\nfirewall:\n  default: deny\n  allow: [22]\n",
        encoding="utf-8",
    )

    app = ZeroSysTUI()
    async with app.run_test(size=TEST_SIZE) as pilot:
        input_widget = app.query_one("#config-path", Input)
        input_widget.value = str(config_path)
        await pilot.click("#btn-load")
        await pilot.pause()

        await pilot.click("#btn-apply")
        await pilot.pause()
        assert isinstance(app.screen, ConfirmScreen)

        await pilot.click("#confirm-cancel")
        await pilot.pause()
        assert not isinstance(app.screen, ConfirmScreen)


def test_tui_state_path_uses_platformdirs() -> None:
    path = _default_state_path()

    assert path.name == "state.db"
    assert "0sys" in str(path)
