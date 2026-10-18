from __future__ import annotations

import pytest

from zerosys.tui.app import ZeroSysTUI

pytestmark = pytest.mark.unit


@pytest.mark.asyncio
async def test_tui_app_compose() -> None:
    app = ZeroSysTUI()
    async with app.run_test() as pilot:
        assert app.query_one("#btn-load") is not None
        assert app.query_one("#btn-plan") is not None
        assert app.query_one("#log") is not None

        await pilot.click("#btn-plan")
