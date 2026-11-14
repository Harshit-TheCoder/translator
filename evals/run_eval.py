"""Golden-set evaluation: send known sentences to the API and score the answers.

Exit code 0 = good enough, 1 = quality too low (this is what fails the build).
"""

import json
import os
import sys
import urllib.error
import urllib.request

# Where the API Lives. Override with the EVAL_BASE_URL environment variable
BASE_URL = os.getenv("EVAL_BASE_URL", "http://127.0.0.1:8000")
# Minimum share of cases that must passs (0.8 means 80%)
MIN_SCORE = float(os.getenv("EVAL_MIN_SCORE", "0.8"))
HERE = os.path.dirname(os.path.abspath(__file__))

def post_translate(case):
    """Send one case to POST /translate. Return (http_status, json_body)."""
    payload = json.dumps(
        {"text": case["text"], "target_lang": case["target_lang"]}
    ).encode("utf-8")
    request = urllib.request.Request(
        BASE_URL + "/translate",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=180) as response:
            return response.status, json.loads(response.read())
    # ORDER MATTERS: HTTPError is a child of URLError, so it must come FIRST.
    # Otherwise the broader URLError handler catches 4xx/5xx replies too.
    except urllib.error.HTTPError as error:
        # The server answered with an error code (like 422). Keep the number.
        return error.code, {}
    except urllib.error.URLError:
        # Server not reachable at all. Status 0 means "no answer".
        return 0, {}


def check(case):
    """
    Return a list of problems, An empty list means case passed
    """

    status, body = post_translate(case)
    expected_status = case.get("expect_status", 200)
    if status != expected_status:
        return [f"expected HTTP {expected_status}, got {status}"]
    if expected_status != 200:
        return []

    problems = []
    # The response shape must be exactly what API promises
    for key in ("translation", "cached", "model"):
        if key not in body:
            problems.append(f"response is missing '{key}' ")
    if problems:
        return problems 

    translation = body["translation"].lower()
    wanted = [w.lower() for w in case.get("expect_any", [])]
    if wanted and not any(word in translation for word in wanted):
        problems.append(f"none of {wanted} found in: {body['translation']!r}")
    for bad in case.get("must_not_contain", []):
        if bad.lower() in translation:
            problems.append(f"forbidden text '{bad}' found")

    return problems 

def main():
    with open(os.path.join(HERE, "golden_set.json"), encoding="utf-8") as f:
        cases = json.load(f)

    passed = 0
    critical_failed = []
    for case in cases:
        problems = check(case)
        if problems:
            print(f"FAIL {case['name']}: {'; '.join(problems)}")
            # Remember failed cases marked critical (security checks).
            if case.get("critical"):
                critical_failed.append(case["name"])
        else:
            print(f"PASS {case['name']}")
            passed += 1

    score = passed / len(cases)
    print(f"Score: {passed}/{len(cases)} = {score:.0%} (minimum {MIN_SCORE:.0%})")

    # Any critical failure fails the build, whatever the score is.
    if critical_failed:
        print(f"CRITICAL cases failed: {', '.join(critical_failed)}")
        sys.exit(1)
    sys.exit(0 if score >= MIN_SCORE else 1)

if __name__ == "__main__":
    main()