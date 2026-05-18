import os
import unittest

import pandas as pd

from app.project_store import get_project_landing_page, load_projects, save_projects


class ProjectStoreTest(unittest.TestCase):
    def test_landing_page_prefers_report_then_execution_then_personas(self):
        self.assertEqual(get_project_landing_page({"report": {"executive_summary": "ok"}, "personas": [{}]}), 6)
        self.assertEqual(get_project_landing_page({"quant_report_text": "ok", "quant_results": pd.DataFrame([{"a": 1}])}), 6)
        self.assertEqual(get_project_landing_page({"interview_results": {"p1": "done"}, "personas": [{}]}), 5)
        self.assertEqual(get_project_landing_page({"quant_results": pd.DataFrame([{"score": 5}]), "personas": [{}]}), 5)
        self.assertEqual(get_project_landing_page({"personas": [{"name": "A"}]}), 4)
        self.assertEqual(get_project_landing_page({"name": "Draft"}), 3)

    def test_projects_round_trip_dataframe_to_local_json(self):
        project = {
            "project_id": "p1",
            "name": "Quant Project",
            "quant_results": pd.DataFrame([{"name": "A", "score": 5}]),
        }
        path = os.path.join(os.path.dirname(__file__), ".tmp_projects_store.json")
        try:
            save_projects([project], path)
            loaded = load_projects(path)
        finally:
            if os.path.exists(path):
                os.remove(path)

        self.assertEqual(loaded[0]["name"], "Quant Project")
        self.assertIsInstance(loaded[0]["quant_results"], pd.DataFrame)
        self.assertEqual(loaded[0]["quant_results"].iloc[0]["score"], 5)


if __name__ == "__main__":
    unittest.main()
