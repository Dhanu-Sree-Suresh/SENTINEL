"""
Rule-based intent classifier for analyst requests.

Deliberately NOT an LLM call: every routing decision here needs to be
deterministic, auditable, and explainable to a compliance reviewer
without worrying about prompt injection, hallucinated tool calls, or
non-reproducible behavior (see the "secure the AI agent" concerns in
the platform brief -- excessive agency, hallucinated security
decisions, prompt injection are exactly what an LLM-in-the-loop
router would risk here). A production system MAY use an LLM to help a
human analyst phrase a request in natural language, but the actual
intent -> mechanism -> policy decision path should stay on a
deterministic, testable classifier like this one, with the LLM (if
used at all) strictly upstream of it and never given the authority to
bypass the classifier's decision.

Supported intents:
  - "aggregate_count": a population/statistic count query
      (-> src/agent/dp_query.py, Laplace mechanism)
  - "train_model": a federated classifier training request
      (-> src/fl_engine.py, DP-SGD + secure aggregation)
  - "membership_probe": asks whether a SPECIFIC named/identified
      individual is present in the data -- this is precisely the
      shape of a membership-inference attack query and is REFUSED
      by policy, unconditionally, regardless of any budget available.
      This is a first line of defense on top of (not instead of) the
      statistical query-pattern monitor in src/firewall/query_monitor.py,
      which catches probing that doesn't say so this explicitly.
  - "unknown": doesn't match a supported pattern -> the agent asks
      for clarification rather than guessing and executing something
      unintended (excessive agency mitigation).
"""
import re

MEMBERSHIP_PROBE_PATTERNS = [
    r"\bwas\s+.+\s+in\s+the\s+data\b",
    r"\bis\s+.+\s+(present|included|a member|in the dataset)\b",
    r"\bdoes\s+.+\s+(appear|exist)\s+in\b",
    r"\bcheck\s+if\s+.+\s+is\s+in\b",
    r"\bconfirm\s+.+\s+is\s+(present|a record|in the data)\b",
]

AGGREGATE_PATTERNS = [
    r"\bhow many\b", r"\bcount of\b", r"\bnumber of\b", r"\btotal\b.*\bcount\b",
    r"\bpopulation\b", r"\bstatistic\b", r"\baverage\b", r"\brate of\b",
]

TRAIN_PATTERNS = [
    r"\btrain\b", r"\bbuild a (model|classifier)\b", r"\brun (the )?classifier\b",
    r"\bfederated (learning|training)\b", r"\bupdate the model\b",
]


def classify_intent(request_text):
    text = request_text.strip().lower()

    for pat in MEMBERSHIP_PROBE_PATTERNS:
        if re.search(pat, text):
            return "membership_probe"

    for pat in TRAIN_PATTERNS:
        if re.search(pat, text):
            return "train_model"

    for pat in AGGREGATE_PATTERNS:
        if re.search(pat, text):
            return "aggregate_count"

    return "unknown"
