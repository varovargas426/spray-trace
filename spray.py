"""Find the first password-spray threshold crossing per source."""
import argparse
from collections import Counter, defaultdict, deque
from datetime import datetime, timedelta, timezone
from ipaddress import ip_address
import json
from pathlib import Path


def normalize(row):
    stamp = datetime.fromisoformat(row["time"])
    if stamp.utcoffset() is None:
        raise ValueError("time must include a UTC offset")
    user, outcome = row["user"], row["outcome"]
    if not isinstance(user, str) or not user.strip() or outcome not in ("failure", "success"):
        raise ValueError("expected a user and a success/failure outcome")
    return stamp.astimezone(timezone.utc), str(ip_address(row["ip"])), user, outcome


def investigate(rows, threshold=5, minutes=10):
    if threshold < 2 or minutes < 1:
        raise ValueError("threshold must be >= 2 and minutes >= 1")
    groups = defaultdict(list)
    for when, ip, user, outcome in sorted(map(normalize, rows)):
        groups[ip].append((when, user, outcome))
    span = timedelta(minutes=minutes)
    alerts = []
    for ip, events in groups.items():
        window, counts = deque(), Counter()
        for index, (when, user, outcome) in enumerate(events):
            if outcome != "failure":
                continue
            while window and window[0][0] < when - span:
                _, old = window.popleft()
                counts[old] -= 1
                if not counts[old]:
                    del counts[old]
            window.append((when, user))
            counts[user] += 1
            if len(counts) >= threshold:
                successes = {name for at, name, status in events[index + 1:]
                             if when < at <= when + span and status == "success" and name in counts}
                alerts.append(dict(ip=ip, detected_at=when.isoformat(),
                                   targeted=sorted(counts), later_success=sorted(successes)))
                break
    return alerts


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("log", type=Path)
    parser.add_argument("--threshold", type=int, default=5)
    parser.add_argument("--minutes", type=int, default=10)
    args = parser.parse_args()
    try:
        rows = [json.loads(line) for line in args.log.read_text(encoding="utf-8").splitlines() if line.strip()]
        print(json.dumps(investigate(rows, args.threshold, args.minutes), indent=2))
    except (ValueError, TypeError, KeyError, OSError) as exc:
        parser.exit(2, f"Invalid input: {exc}\n")
