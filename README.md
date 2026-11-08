# Spray Trace

Reconstruct a password spray from identity logs and identify targeted accounts that subsequently signed in from the same address.

## Reproduce the case

Requires Python 3.11+. All examples use synthetic data and run locally with the standard library. Run from the repository root.

```sh
python spray.py examples/sign-ins.jsonl --threshold 3
```

The fixture yields one alert for 192.0.2.8. Three distinct accounts failed within ten minutes. Only alex subsequently signed in from that address during the observation window. The unrelated sign-in from another address stays out of the alert.

## Design and limits

The input is newline-delimited JSON with an offset-aware timestamp, IP address, account and outcome. Events are sorted by time. A per-IP sliding window counts distinct accounts, so repeated attempts against one account do not inflate the signal. The first threshold crossing per IP is reported for this batch. Follow-up successes are leads for investigation. Shared proxies, legitimate retries and missing logs can change their interpretation.

## Verification

```sh
python -m unittest discover -s tests -v
```

Tests cover the window boundary, duplicate attempts, unordered input, address attribution and invalid timestamps.
