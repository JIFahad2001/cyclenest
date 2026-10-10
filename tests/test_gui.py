"""Unit tests for CycleNest CustomTkinter GUI views and navigation.
"""

import unittest
from datetime import date
from cyclenest.gui.app import CycleNestApp


class TestGUI(unittest.TestCase):
    def setUp(self):
        self.app = CycleNestApp(db_path=":memory:")
        self.app.withdraw()  # Don't show window during automated test

    def tearDown(self):
        self.app.destroy()

    def test_all_views_navigate_and_render(self):
        views = [
            "dashboard",
            "log",
            "calendar",
            "predictions",
            "analytics",
            "charts",
            "history",
            "settings",
        ]
        for v in views:
            self.app.navigate(v)
            self.app.update()

    def test_navigate_to_specific_date(self):
        test_d = date(2026, 10, 5)
        self.app.navigate("log", test_d)
        self.app.update()
        log_view = self.app.views["log"]
        self.assertEqual(log_view.current_date, test_d)

    def test_charts_view_render(self):
        self.app.navigate("charts")
        self.app.update()
        charts_view = self.app.views["charts"]
        for tab in ["Cycle Lengths", "BBT Temperature", "Symptoms", "Pain Profile"]:
            charts_view._on_tab_change(tab)
            self.app.update()


if __name__ == "__main__":
    unittest.main()
