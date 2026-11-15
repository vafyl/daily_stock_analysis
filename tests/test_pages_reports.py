import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile

from scripts.collect_pages_reports import collect_github_reports, read_archive, write_index


class PagesReportsTests(unittest.TestCase):
    def archive(self, entries):
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w") as archive:
            for filename, content in entries.items():
                archive.writestr(filename, content)
        return buffer.getvalue()

    def test_only_expected_report_files_are_published(self):
        archive = self.archive({
            "reports/report_20261115.md": "# 股票报告",
            "reports/market_review_20261115.md": "# 大盘复盘",
            "logs/stock_analysis.log": "SECRET_VALUE",
            "reports/.env": "SECRET_VALUE",
            "reports/../report_20261115.md": "SECRET_VALUE",
            "reports/report_20261315.md": "Invalid date",
            "reports/arbitrary.md": "SECRET_VALUE",
            "reports/report_20261114.md": "   ",
        })
        reports = read_archive(archive, "https://github.com/example/repo/actions/runs/1")
        self.assertEqual({report["kind"] for report in reports}, {"stocks", "market"})
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            write_index(reports, output, "example/repo")
            self.assertEqual({path.name for path in output.iterdir()}, {
                "index.json", "report_20261115.md", "market_review_20261115.md",
            })
            payload = json.loads((output / "index.json").read_text())
            self.assertEqual(payload["reports"][0]["kind"], "stocks")
            self.assertNotIn("SECRET_VALUE", (output / "index.json").read_text())

    def test_empty_archive_does_not_replace_existing_site(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            (output / "index.json").write_text("existing")
            with self.assertRaises(ValueError):
                write_index([], output, "example/repo")
            self.assertEqual((output / "index.json").read_text(), "existing")

    def test_only_trusted_runs_and_latest_report_are_collected(self):
        def run(number, event="workflow_dispatch", repository="example/repo"):
            return {
                "id": number,
                "run_number": number,
                "event": event,
                "head_repository": {"full_name": repository},
                "html_url": f"https://github.com/example/repo/actions/runs/{number}",
            }

        def response(endpoint):
            if "/workflows/" in endpoint:
                return {"workflow_runs": [run(4, event="pull_request"), run(3, repository="other/repo"), run(2), run(1)]}
            number = int(endpoint.split("/")[-2])
            return {"artifacts": [
                {"id": 99, "name": "unrelated", "expired": False},
                {"id": 98, "name": f"analysis-reports-{number}", "expired": True},
                {"id": number, "name": f"analysis-reports-{number}", "expired": False},
            ]}

        with patch("scripts.collect_pages_reports.github_json", side_effect=response) as api:
            with patch("scripts.collect_pages_reports.subprocess.check_output", side_effect=[
                self.archive({"reports/report_20261115.md": "Latest"}),
                self.archive({"reports/report_20261115.md": "Older"}),
            ]) as download:
                reports = collect_github_reports("example/repo", "main")
        self.assertEqual(api.call_count, 3)
        self.assertEqual(download.call_count, 2)
        self.assertEqual(len(reports), 1)
        self.assertEqual(reports[0]["markdown"], "Latest")
        self.assertTrue(reports[0]["runUrl"].endswith("/2"))


if __name__ == "__main__":
    unittest.main()
