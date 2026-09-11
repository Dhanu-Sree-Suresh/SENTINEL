"""
Live demo of the privacy-aware agent against the REAL generated
dataset (not mocked), showing:
  - a legitimate aggregate query answered with DP noise
  - a membership-inference-shaped request refused outright
  - a differencing-attack query sequence detected and blocked
  - a training request handed off to the FL pipeline
  - the full audit trail this produces

Run with:  python3 -m experiments.run_agent_demo
"""
import json
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data_gen import generate_all
from src.agent.agent import PrivacyAwareAgent
from src.firewall.budget_ledger import BudgetLedger
from src.firewall.query_monitor import QueryMonitor
from src.provenance import get_provenance

RESULTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results")
os.makedirs(RESULTS_DIR, exist_ok=True)


def main():
    print("=" * 70)
    print("Generating dataset and standing up the agent ...")
    df = generate_all(seed=42, scale=0.05)  # small/fast for an interactive demo
    entity_dfs = {e: df[df.entity == e].reset_index(drop=True) for e in df.entity.unique()}

    ledger = BudgetLedger(list(entity_dfs.keys()), tier="normal")
    monitor = QueryMonitor(window_seconds=60, freq_threshold=5, jaccard_threshold=0.65)  # see query_monitor.py docstring for why 0.65, not the textbook 0.8, is the justified default
    agent = PrivacyAwareAgent(entity_dfs, ledger, monitor, query_epsilon=0.5)

    transcript = []

    def ask(analyst, text, filters=None, ts=None):
        resp = agent.handle_request(analyst, text, filters=filters, ts=ts)
        entry = dict(analyst=analyst, request=text, **resp.to_dict())
        transcript.append(entry)
        print(f"\n[{analyst}] \"{text}\"")
        print(f"  -> allowed={resp.allowed}  intent={resp.intent}")
        if resp.result:
            print(f"  -> result: {resp.result}")
        print(f"  -> explanation: {resp.explanation}")
        return resp

    print("\n--- Scenario 1: legitimate aggregate query ---")
    ask("soc_analyst_1", "How many insider-threat flags do we have?", filters={"query": "total"})

    print("\n--- Scenario 2: membership-inference-shaped request (refused by policy) ---")
    ask("curious_user", "Was employee 00042 in the data?")

    print("\n--- Scenario 3: differencing-attack query sequence (detected mid-sequence) ---")
    base = {"region": "dubai", "department": "licensing"}
    for i in range(6):
        filt = dict(base)
        if i >= 2:
            filt["exclude_id"] = f"person_{i}"
        ask("probing_analyst", "how many flags in this group?", filters=filt, ts=i * 5.0)

    print("\n--- Scenario 4: model-training request (handed off to the FL pipeline) ---")
    ask("ml_engineer", "Please train the classifier across all entities")

    print("\n--- Final budget ledger state ---")
    print(json.dumps(ledger.summary(), indent=2))

    with open(os.path.join(RESULTS_DIR, "agent_demo_transcript.json"), "w") as f:
        json.dump({"transcript": transcript, "final_ledger": ledger.summary(),
                   "monitor_alerts": monitor.alerts,
                   "provenance": get_provenance(experiment="run_agent_demo")},
                  f, indent=2, default=str)
    print("\nSaved agent_demo_transcript.json to", RESULTS_DIR)


if __name__ == "__main__":
    main()
