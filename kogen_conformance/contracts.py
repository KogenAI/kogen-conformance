"""v1.3 observation oracles; no implementation imports or credential access."""
import json


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def reusable_prefix(requests, cross_session=False, forbidden=()):
    errors = []
    if len(requests) < 2:
        return ["prefix: need at least two provider requests"]
    prefixes, threads = [], []
    for r in requests:
        b = r.get("body", {})
        items = b.get("input", [])
        # A separate leading developer item provides an observable static/role boundary.
        instruction_items = [i for i in items if not (isinstance(i, dict) and i.get("type") == "additional_tools")]
        first = instruction_items[0] if instruction_items else {}
        leading = isinstance(first, dict) and first.get("role") in ("developer", "system")
        instructions = b.get("instructions")
        generic = first if leading else instructions
        if cross_session and isinstance(generic, str):
            # A string codec can separate generic and role instructions by paragraphs.
            generic = generic.split("\n\n", 1)[0]
        content = generic
        if not content:
            errors.append("prefix: empty generic instructions")
        tools = b.get("tools", [])
        if not isinstance(tools, list):
            tools = []
        for item in items:
            if isinstance(item, dict) and item.get("type") == "additional_tools":
                tools = tools + item.get("tools", [])
        required = {"edit", "read", "search", "write", "shell", "finish", "tool_output"}
        names = {t.get("name") for t in tools if isinstance(t, dict)} if isinstance(tools, list) else set()
        if required != names or len(tools) != len(required):
            errors.append("prefix: missing complete canonical tool definitions")
        if any(not isinstance(t, dict) or not isinstance(t.get("parameters"), dict) for t in tools):
            errors.append("prefix: tool definitions omit their schemas")
        prefix = canonical([generic, tools])
        if any(v and v in prefix for v in forbidden):
            errors.append("prefix: variable task/run/path data precedes static boundary")
        prefixes.append(prefix)
        thread = r.get("headers", {}).get("thread-id")
        if not thread:
            errors.append("prefix: missing conversation identity")
        threads.append(thread)
        if b.get("store") is not False or "previous_response_id" in b:
            errors.append("prefix: stateful request or previous_response_id")
    if len(set(prefixes)) != 1:
        errors.append("prefix: generic instructions or canonical schemas changed")
    if cross_session:
        if len(set(threads)) != len(threads):
            errors.append("prefix: independent invocations reuse a thread")
    else:
        if len(set(threads)) != 1:
            errors.append("prefix: thread changed within conversation")
        for a, b in zip(requests, requests[1:]):
            old, new = a["body"], b["body"]
            before, after = old.get("input"), new.get("input")
            if not isinstance(before, list) or not isinstance(after, list) or after[:len(before)] != before:
                errors.append("prefix: history rewritten rather than appended")
            for key in ("instructions", "tools", "model", "reasoning", "store", "stream", "include", "prompt_cache_key", "tool_choice"):
                if old.get(key) != new.get(key):
                    errors.append("prefix: same-conversation %s changed" % key)
    return errors


def observational(report, events, require_warning=False):
    errors = []
    if report.get("advisory_items") != []:
        errors.append("audit: advisory_items must be empty")
    if not report.get("acceptance") or any(i.get("demoted") is not False for i in report["acceptance"]):
        errors.append("audit: all approved items must remain undemoted")
    if report.get("verdict") == "green-with-advisory-tests":
        errors.append("audit: reserved advisory verdict")
    if require_warning:
        warnings = [report.get("findings", []), report.get("warnings", [])] + [e for e in events if e.get("event") == "audit"]
        if "warn" not in canonical(warnings).lower():
            errors.append("audit: malformed/unknown/duplicate replies require a warning")
    for e in events:
        if e.get("event") == "acceptance_demoted":
            errors.append("audit: acceptance_demoted is forbidden")
        if e.get("event") == "audit" and e.get("mode") != "observational":
            errors.append("audit: receipt lacks observational mode")
    return errors


def shape_accounting(receipt, expected, requests, wall_ms):
    """The suite's neutral receipt projection is documented in data/v1.3/RECEIPTS.md."""
    from .matchers import match
    if not isinstance(receipt, dict):
        return ["shape: receipt must be an object"]
    errors = ["shape: " + e for e in match(expected, receipt)]
    if receipt.get("schema") != 1 or receipt.get("profile") != "shape-v1.3":
        errors.append("shape: missing schema 1 / shape-v1.3")
    cs = receipt.get("conversations", [])
    if not isinstance(cs, list) or not cs or len(cs) > 2:
        return errors + ["shape: one or two conversations required"]
    ids = [c.get("conversation_id") for c in cs]
    if any(not i for i in ids) or len(set(ids)) != len(ids):
        errors.append("shape: fresh conversation identities required")
    for c in cs:
        if not isinstance(c, dict):
            return errors + ["shape: conversation receipt must be an object"]
        if not 0 <= c.get("logical_turns", -1) <= 60 or not 0 <= c.get("validation_passes", -1) <= 3:
            errors.append("shape: turn/pass allowance exceeded or missing")
        if not 0 <= c.get("style_repairs", -1) <= 2:
            errors.append("shape: style allowance exceeded or missing")
    if receipt.get("http_attempts") != len(requests):
        errors.append("shape: every HTTP attempt, including failure, must be counted")
    if receipt.get("validation_passes") != sum(c.get("validation_passes", 0) for c in cs):
        errors.append("shape: totals count actual traversals, not fallback slot labels")
    # Receipt elapsed time includes the whole CLI operation, allowing timer precision.
    elapsed = receipt.get("elapsed_ms")
    if not isinstance(elapsed, int) or elapsed < max(0, wall_ms - 1000):
        errors.append("shape: elapsed time omits setup/validation/waits")
    for field in ("roles", "repairs", "tokens", "unknown_usage_attempts", "finish_guards", "outcome"):
        if field not in receipt:
            errors.append("shape: missing " + field)
    if all("fixture_usage" in r for r in requests):
        totals = {"input": 0, "cached_input": 0, "output": 0, "reasoning": 0}
        unknown = 0
        for request in requests:
            usage = request["fixture_usage"] or {}
            total = usage.get("input_tokens")
            cached = (usage.get("input_tokens_details") or {}).get("cached_tokens")
            output = usage.get("output_tokens")
            reasoning = (usage.get("output_tokens_details") or {}).get("reasoning_tokens")
            values = {"input": total - cached if total is not None and cached is not None and total >= cached else None,
                      "cached_input": cached, "output": output, "reasoning": reasoning}
            unknown += any(v is None for v in values.values())
            for key, value in values.items():
                if value is not None:
                    totals[key] += value
        if receipt.get("unknown_usage_attempts") != unknown:
            errors.append("shape: unknown/failed attempt usage was dropped or invented")
        for key, total in totals.items():
            if receipt.get("tokens", {}).get(key) != total:
                errors.append("shape: known token total differs for " + key)
    return errors


def measure_cache(replay):
    """Offline accounting boundary (§4.9.5), never a fake live-release qualification."""
    required = ("spec", "adapter", "prompt", "replay", "provider", "model", "endpoint", "namespace", "affinity", "retention", "tokenizer", "minimum", "block", "appended_budget")
    if any(k not in replay for k in required):
        raise ValueError("freeze all replay identities and eligibility rules")
    block, minimum = replay["block"], replay["minimum"]
    if type(block) is not int or block <= 0 or type(minimum) is not int or minimum < 0:
        raise ValueError("invalid adapter block/minimum")
    rows = []
    for i, r in enumerate(replay["requests"], 1):
        p, t, c = r.get("prefix_tokens"), r.get("total_input"), r.get("cached_input")
        known = r.get("eligibility_known", True) and p is not None
        eligible = (0 if p < minimum else (p // block) * block) if known else None
        warm = r.get("designated_warm", False)
        if warm and i < 3:
            raise ValueError("designated warm requests must be third or later")
        if warm and (eligible is None or t is None or t <= 0 or eligible / t < .95 or t - p > replay["appended_budget"]):
            raise ValueError("infeasible frozen warm request or appended-token budget")
        usage = t is not None and c is not None and t >= 0 and 0 <= c <= t
        complete = known and usage
        status = "incomplete" if not complete else ("miss" if c == 0 and eligible else "measured")
        qualification = ("incomplete" if not complete else ("pass" if t and c / t >= .95 else "fail")) if warm else "inapplicable"
        rows.append({"request": i, "total_input": t, "cached_input": c, "eligible_input": eligible,
                     "raw_hit_rate": c / t if usage and t else None,
                     "eligible_prefix_reuse": min(c, eligible) / eligible if complete and eligible else None,
                     "excess_cached_input": max(0, c - eligible) if complete else None,
                     "measurement": status, "qualification": qualification,
                     "zero_eligible": eligible == 0, "conversation_id": r.get("conversation_id")})
    known_rows = [r for r in rows if r["raw_hit_rate"] is not None]
    total = sum(r["total_input"] for r in known_rows)
    return {"versions": {k: replay[k] for k in required}, "live_release_qualified": False,
            "requests": rows, "weighted_hit_rate": sum(r["cached_input"] for r in known_rows) / total if total else None,
            "partial": len(known_rows) != len(rows),
            "qualification": "incomplete" if any(r["qualification"] == "incomplete" for r in rows) else
                "fail" if any(r["qualification"] == "fail" for r in rows) else
                "pass" if any(r["qualification"] == "pass" for r in rows) else "inapplicable"}
