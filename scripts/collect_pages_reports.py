import argparse
from datetime import datetime, timezone
import io
import json
from pathlib import Path
import re
import subprocess
import zipfile


REPORT_PATH = re.compile(r"reports/(?P<kind>report|market_review)_(?P<date>\d{8})\.md")
MAX_REPORT_BYTES = 2 * 1024 * 1024


def github_json(endpoint):
    return json.loads(subprocess.check_output(["gh", "api", endpoint]))


def read_archive(archive_bytes, run_url):
    reports = []
    with zipfile.ZipFile(io.BytesIO(archive_bytes)) as archive:
        for entry in archive.infolist():
            match = REPORT_PATH.fullmatch(entry.filename)
            if not match or entry.file_size > MAX_REPORT_BYTES:
                continue
            try:
                report_date = datetime.strptime(match["date"], "%Y%m%d").date().isoformat()
            except ValueError:
                continue
            content = archive.read(entry).decode("utf-8").strip()
            if not content:
                continue
            filename = Path(entry.filename).name
            kind = "stocks" if match["kind"] == "report" else "market"
            reports.append({
                "id": Path(filename).stem,
                "date": report_date,
                "kind": kind,
                "title": "个股研报" if kind == "stocks" else "大盘复盘",
                "markdown": content,
                "download": filename,
                "runUrl": run_url,
            })
    return reports


def collect_github_reports(repository, branch):
    runs = github_json(
        f"repos/{repository}/actions/workflows/00-daily-analysis.yml/runs"
        f"?branch={branch}&status=success&per_page=100"
    )["workflow_runs"]
    reports = {}
    for run in runs:
        if run["event"] not in {"schedule", "workflow_dispatch"}:
            continue
        if run.get("head_repository", {}).get("full_name") != repository:
            continue
        artifacts = github_json(f"repos/{repository}/actions/runs/{run['id']}/artifacts")["artifacts"]
        for artifact in artifacts:
            if artifact["expired"] or artifact["name"] != f"analysis-reports-{run['run_number']}":
                continue
            archive = subprocess.check_output([
                "gh", "api", f"repos/{repository}/actions/artifacts/{artifact['id']}/zip",
            ])
            for report in read_archive(archive, run["html_url"]):
                reports.setdefault(report["id"], report)
    return list(reports.values())


def write_index(reports, output, repository):
    if not reports:
        raise ValueError("No published reports found; keeping the existing Pages deployment.")
    output.mkdir(parents=True, exist_ok=True)
    reports.sort(key=lambda report: (report["date"], report["kind"] == "stocks"), reverse=True)
    for report in reports:
        (output / report["download"]).write_text(report["markdown"] + "\n", encoding="utf-8")
    index = {
        "publishedAt": datetime.now(timezone.utc).isoformat(),
        "workflowUrl": f"https://github.com/{repository}/actions/workflows/00-daily-analysis.yml",
        "reports": reports,
    }
    (output / "index.json").write_text(json.dumps(index, ensure_ascii=False), encoding="utf-8")
    print(f"Prepared {len(reports)} reports for publication.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository", required=True)
    parser.add_argument("--branch", default="main")
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--archive", type=Path)
    parser.add_argument("--run-url", default="")
    args = parser.parse_args()
    reports = (
        read_archive(args.archive.read_bytes(), args.run_url)
        if args.archive else collect_github_reports(args.repository, args.branch)
    )
    write_index(reports, args.output, args.repository)


if __name__ == "__main__":
    main()
