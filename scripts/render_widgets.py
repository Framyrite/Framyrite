"""Render a profile activity card from public GitHub commits."""

import argparse
from collections import Counter, defaultdict
from datetime import datetime, time, timedelta
from html import escape
import json
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

MOSCOW = ZoneInfo("Europe/Moscow")
ASSETS = Path(__file__).resolve().parents[1] / "assets"
PAGE_SIZE = 100
REPOSITORY_LIMIT = 5
EXCLUDED_REPOSITORIES = {"framyrite/projectdesk", "crucifiedshepherd/projectdesk"}
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


def github_commits(login, earliest, now):
    query = f"author:{login} committer-date:{earliest.isoformat()}..{now.isoformat()}"
    for page in range(1, 11):
        params = urlencode({
            "q": query,
            "sort": "committer-date",
            "order": "desc",
            "page": page,
            "per_page": PAGE_SIZE,
        })
        request = Request(
            f"https://api.github.com/search/commits?{params}",
            headers={
                "Accept": "application/vnd.github+json",
                "User-Agent": "Framyrite-Profile-Activity",
            },
        )
        with urlopen(request, timeout=15) as response:
            data = json.load(response)
        if data["incomplete_results"] or data["total_count"] > 1000:
            raise RuntimeError("The GitHub commit search did not return a complete result.")
        yield from data["items"]
        if page * PAGE_SIZE >= data["total_count"]:
            return


def moscow_time(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(MOSCOW)


def repository_commits(login, start, now):
    earliest = datetime.combine(start, time.min, MOSCOW)
    excluded = EXCLUDED_REPOSITORIES | {f"{login}/{login}".casefold()}
    repositories = defaultdict(list)
    seen = set()
    for item in github_commits(login, earliest, now):
        name = item["repository"]["full_name"]
        if name.casefold() in excluded or item["repository"]["private"] or item["sha"] in seen:
            continue
        timestamp = moscow_time(item["commit"]["committer"]["date"])
        if earliest <= timestamp <= now:
            repositories[name].append(timestamp)
            seen.add(item["sha"])

    recent = sorted(
        repositories.items(),
        key=lambda repo: (max(repo[1]), repo[0]),
        reverse=True,
    )
    return recent[:REPOSITORY_LIMIT]


def activity(repositories, start):
    counts = Counter(
        (timestamp.date() - start).days // 7
        for _, timestamps in repositories
        for timestamp in timestamps
    )
    peak = max(counts.values(), default=1)
    last = (
        f"Последний коммит · {max(repositories[0][1]):%d.%m.%Y}"
        if repositories
        else "За этот период нет коммитов"
    )
    elements = [
        f'<text x="27" y="38" font-size="22" font-weight="600" fill="{INK}">Мои коммиты за 12 недель</text>',
        f'<text x="27" y="63" font-size="16" fill="{MUTED}">{last}</text>',
        '<path d="M26 100h487M26 148h487M26 196h487M534 25v205" stroke="#d8dee4"/>',
        f'<text x="555" y="38" font-size="17" font-weight="600" fill="{INK}">Недавние репозитории</text>',
    ]
    for index in range(12):
        x = 36 + index * 40
        count = counts[index]
        if count:
            height = max(1, 94 * count / peak)
            top = 195 - height
            elements.append(
                f'<rect x="{x}" y="{top:.2f}" width="22" height="{height:.2f}" rx="1" fill="{ORANGE}"/>'
            )
            elements.append(
                f'<text x="{x + 11}" y="{top - 5:.2f}" text-anchor="middle" font-size="12" fill="{MUTED}">{count}</text>'
            )
        if index in (0, 3, 7, 11):
            week = start + timedelta(weeks=index)
            elements.append(
                f'<text x="{x + 11}" y="222" text-anchor="middle" font-size="14" fill="{MUTED}">{week:%d.%m}</text>'
            )

    for index, (name, timestamps) in enumerate(repositories):
        y = 74 + index * 34
        name = name.split("/", 1)[-1]
        label = escape(name if len(name) <= 29 else name[:28] + "…")
        elements.append(
            f'<text x="555" y="{y}" font-family="monospace" font-size="14" fill="{INK}">{label}</text>'
        )
        elements.append(
            f'<text x="852" y="{y}" text-anchor="end" font-size="15" fill="{MUTED}">{len(timestamps)}</text>'
        )
    body = "\n    ".join(elements)
    total = sum(counts.values())
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="880" height="250" viewBox="0 0 880 250" role="img" aria-labelledby="title desc">
  <title id="title">Мои коммиты за 12 недель</title>
  <desc id="desc">Число коммитов: {total}. Репозиториев: {len(repositories)}. {last}.</desc>
  <rect x="1" y="1" width="878" height="248" rx="12" fill="#ffffff" stroke="#d8dee4" stroke-width="2"/>
  <g font-family="Arial,sans-serif">
    {body}
  </g>
</svg>
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("login")
    args = parser.parse_args()
    now = datetime.now(MOSCOW)
    today = now.date()
    start = today - timedelta(days=today.weekday() + 77)
    light = activity(repository_commits(args.login, start, now), start)
    dark = light
    for light_color, dark_color in LIGHT_TO_DARK.items():
        dark = dark.replace(light_color, dark_color)
    (ASSETS / "activity.svg").write_text(light, encoding="utf-8")
    (ASSETS / "activity-dark.svg").write_text(dark, encoding="utf-8")


if __name__ == "__main__":
    main()
