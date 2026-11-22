"""Render the profile widgets from the default branches of two public repos."""

import argparse
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path
import subprocess
from zoneinfo import ZoneInfo

MOSCOW = ZoneInfo("Europe/Moscow")
PROJECTS = ("FinDocs", "ProjectDesk")
ASSETS = Path(__file__).resolve().parents[1] / "assets"
COLORS = ("#bf4a1c", "#f0a575")
INK = "#2c2520"
MUTED = "#685c53"


def history(repo):
    output = subprocess.check_output(
        ["git", "-C", str(repo), "log", "--format=%H %cI", "HEAD"],
        text=True,
    )
    return [
        (sha, datetime.fromisoformat(timestamp).astimezone(MOSCOW))
        for sha, timestamp in (line.split() for line in output.splitlines())
    ]


def svg(height, label, body):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="620" height="{height}" viewBox="0 0 620 {height}" role="img" aria-labelledby="title">
  <title id="title">{label}</title>
  <rect x="1" y="1" width="618" height="{height - 2}" rx="11" fill="#fffdf9" stroke="#decec0" stroke-width="2"/>
  <g font-family="Arial,sans-serif">
{body}
  </g>
</svg>
'''


def activity(histories, today):
    start = today - timedelta(days=today.weekday() + 77)
    weeks = [start + timedelta(weeks=index) for index in range(12)]
    counts = [
        Counter(
            (timestamp.date() - start).days // 7
            for _, timestamp in commits
            if start <= timestamp.date() <= today
        )
        for commits in histories
    ]
    peak = max(1, *(sum(series[index] for series in counts) for index in range(12)))
    elements = [
        f'<text x="24" y="36" font-size="19" font-weight="600" fill="{INK}">12 недель · коммиты в основных ветках</text>',
        '<path d="M25 67h570M25 110h570M25 153h570" stroke="#e7dcd1"/>',
    ]
    for index, week in enumerate(weeks):
        x = 31 + index * 47
        bottom = 152.0
        for series, color in zip(counts, COLORS):
            count = series[index]
            if count:
                height = 84 * count / peak
                bottom -= height
                elements.append(
                    f'<rect x="{x}" y="{bottom:.2f}" width="28" height="{height:.2f}" fill="{color}"/>'
                )
        total = sum(series[index] for series in counts)
        if total:
            elements.append(
                f'<text x="{x + 14}" y="{bottom - 5:.2f}" text-anchor="middle" font-size="11" fill="{MUTED}">{total}</text>'
            )
        if index in (0, 3, 7, 11):
            elements.append(
                f'<text x="{x + 14}" y="174" text-anchor="middle" font-size="12" fill="{MUTED}">{week:%d.%m}</text>'
            )
    for index, (name, color) in enumerate(zip(PROJECTS, COLORS)):
        x = 26 + index * 100
        elements.extend([
            f'<rect x="{x}" y="192" width="11" height="11" rx="2" fill="{color}"/>',
            f'<text x="{x + 18}" y="202" font-size="13" fill="{MUTED}">{name}</text>',
        ])
    return svg(222, "Коммиты по неделям — FinDocs и ProjectDesk", "\n".join(elements))


def latest(histories):
    timestamp, name, sha = max(
        (timestamp, name, sha)
        for name, commits in zip(PROJECTS, histories)
        for sha, timestamp in commits
    )
    return svg(
        98,
        f"Последний коммит: {name}, {timestamp:%d.%m.%Y}, {sha[:7]}",
        f'''    <circle cx="32" cy="28" r="5" fill="{COLORS[0]}"/>
    <text x="46" y="33" font-size="15" fill="{MUTED}">Последний коммит · основная ветка</text>
    <text x="27" y="70" font-size="23" font-weight="600" fill="{INK}">{name}</text>
    <text x="593" y="69" text-anchor="end" font-family="monospace" font-size="15" fill="{MUTED}">{timestamp:%d.%m.%Y} · {sha[:7]}</text>''',
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("findocs", type=Path)
    parser.add_argument("projectdesk", type=Path)
    args = parser.parse_args()
    histories = [history(args.findocs), history(args.projectdesk)]
    today = datetime.now(MOSCOW).date()
    (ASSETS / "activity.svg").write_text(activity(histories, today), encoding="utf-8")
    (ASSETS / "latest.svg").write_text(latest(histories), encoding="utf-8")


if __name__ == "__main__":
    main()
