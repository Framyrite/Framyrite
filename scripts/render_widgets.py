"""Render the FinDocs activity card from the public default branch."""

import argparse
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path
import subprocess
from zoneinfo import ZoneInfo

MOSCOW = ZoneInfo("Europe/Moscow")
ASSETS = Path(__file__).resolve().parents[1] / "assets"
LIGHT_TO_DARK = {
    "#ffffff": "#171a1f",
    "#d8dee4": "#343b45",
    "#24292f": "#f0f3f6",
    "#57606a": "#b0b7c3",
    "#b84316": "#ff8a4c",
}
INK = "#24292f"
MUTED = "#57606a"
ORANGE = "#b84316"


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
        '<path d="M28 66h824M28 107h824M28 148h824" stroke="#d8dee4"/>',
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
  <rect x="1" y="1" width="878" height="192" rx="12" fill="#ffffff" stroke="#d8dee4" stroke-width="2"/>
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
    light = activity(history(args.findocs), today)
    dark = light
    for light_color, dark_color in LIGHT_TO_DARK.items():
        dark = dark.replace(light_color, dark_color)
    (ASSETS / "activity.svg").write_text(light, encoding="utf-8")
    (ASSETS / "activity-dark.svg").write_text(dark, encoding="utf-8")


if __name__ == "__main__":
    main()
