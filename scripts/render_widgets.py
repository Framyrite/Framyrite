"""Render the FinDocs activity card from the public default branch."""

import argparse
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path
import subprocess
from zoneinfo import ZoneInfo

MOSCOW = ZoneInfo("Europe/Moscow")
ASSET = Path(__file__).resolve().parents[1] / "assets" / "activity.svg"
INK = "#2a221d"
MUTED = "#685950"
ORANGE = "#bb471d"


def history(repo):
    output = subprocess.check_output(
        ["git", "-C", str(repo), "log", "--format=%H %cI", "HEAD"],
        text=True,
    )
    return [
        (sha, datetime.fromisoformat(timestamp).astimezone(MOSCOW))
        for sha, timestamp in (line.split() for line in output.splitlines())
    ]


def activity(commits, today):
    start = today - timedelta(days=today.weekday() + 77)
    weeks = [start + timedelta(weeks=index) for index in range(12)]
    counts = Counter(
        (timestamp.date() - start).days // 7
        for _, timestamp in commits
        if start <= timestamp.date() <= today
    )
    latest_sha, latest_at = max(commits, key=lambda commit: commit[1])
    peak = max(counts.values(), default=1)
    elements = [
        f'<text x="29" y="38" font-size="21" font-weight="600" fill="{INK}">Коммиты за 12 недель</text>',
        f'<text x="851" y="38" text-anchor="end" font-size="17" fill="{MUTED}">Последний · {latest_at:%d.%m.%Y} · {latest_sha[:7]}</text>',
        '<path d="M28 66h824M28 107h824M28 148h824" stroke="#e7dcd1"/>',
    ]
    for index, week in enumerate(weeks):
        x = 45 + index * 69
        count = counts[index]
        if count:
            height = max(1, 81 * count / peak)
            top = 147 - height
            elements.append(
                f'<rect x="{x}" y="{top:.2f}" width="32" height="{height:.2f}" rx="1" fill="{ORANGE}"/>'
            )
            elements.append(
                f'<text x="{x + 16}" y="{top - 5:.2f}" text-anchor="middle" font-size="13" fill="{MUTED}">{count}</text>'
            )
        if index in (0, 3, 7, 11):
            elements.append(
                f'<text x="{x + 16}" y="173" text-anchor="middle" font-size="15" fill="{MUTED}">{week:%d.%m}</text>'
            )
    body = "\n    ".join(elements)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="880" height="194" viewBox="0 0 880 194" role="img" aria-labelledby="title">
  <title id="title">Активность FinDocs · последний коммит {latest_at:%d.%m.%Y}</title>
  <rect x="1" y="1" width="878" height="192" rx="12" fill="#fffaf4" stroke="#e2d7ca" stroke-width="2"/>
  <g font-family="Arial,sans-serif">
    {body}
  </g>
</svg>
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("findocs", type=Path)
    args = parser.parse_args()
    today = datetime.now(MOSCOW).date()
    ASSET.write_text(activity(history(args.findocs), today), encoding="utf-8")


if __name__ == "__main__":
    main()
