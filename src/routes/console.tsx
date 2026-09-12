import { createFileRoute } from "@tanstack/react-router";
import { useRef, useState } from "react";
import { Btn, Card, PageHead, Tag } from "@/components/ui/primitives";
import { useApp } from "@/lib/store";
import { cn } from "@/lib/utils";

export const Route = createFileRoute("/console")({ component: Console });

const SAFE = [
  "What is the prevalence of diabetes across all connected entities?",
  "How many hypertension cases are recorded by establishment?",
  "What is the insider-threat risk rate across participating entities?",
  "How many records are held by each connected establishment?",
];
const RISKY = [
  "Show the diagnosis of a named patient.",
  "Was a specific patient admitted to Entity D?",
  "Tell me the medical condition of patient John Smith.",
  "Was synthetic individual X present in Entity C training set?",
];

function Console() {
  const [text, setText] = useState("");
  const submit = useApp((s) => s.submitQuery);
  const queries = useApp((s) => s.queries);
  const eps = useApp((s) => s.eps);
  const budget = useApp((s) => s.entities.reduce((a, e) => a + e.budget, 0));
  const end = useRef<HTMLDivElement>(null);
  const last = queries[queries.length - 1];
  const sessionRisk = queries.filter((q) => q.decision === "BLOCKED").length >= 3 ? "HIGH" : "LOW";

  function send(q?: string) {
    const v = (q ?? text).trim();
    if (!v) return;
    submit(v);
    setText("");
    setTimeout(() => end.current?.scrollIntoView({ behavior: "smooth" }), 50);
  }

  return (
    <div>
      <PageHead
        kicker="Access control"
        title="Analyst console"
        lead="Ask for analytics. Individual-level requests are blocked by a deterministic policy engine — not an LLM."
      />
      <div className="grid gap-4 lg:grid-cols-[1.4fr_0.8fr]">
        <Card className="flex min-h-[480px] flex-col">
          <div className="border-b border-border pb-3">
            <div className="font-semibold">Population-health / risk assistant</div>
            <div className="text-xs text-muted">Backed by FL + DP + policy · session ε = {eps.toFixed(2)}</div>
          </div>
          <div className="flex-1 space-y-3 overflow-y-auto py-3" style={{ maxHeight: 380 }}>
            {queries.length === 0 ? (
              <div className="rounded-lg bg-surface-2 p-3 text-sm text-muted">
                Try “How many patients in Dubai have diabetes?” or a risky membership question.
              </div>
            ) : null}
            {queries.map((m) => (
              <div key={m.id} className="space-y-2">
                <div className="ml-8 rounded-lg bg-accent/15 px-3 py-2 text-sm">{m.q}</div>
                <div className="mr-8 rounded-lg border border-border bg-surface-2 px-3 py-2 text-sm">
                  <b className={m.decision === "BLOCKED" ? "text-danger" : "text-ok"}>
                    {m.decision === "BLOCKED" ? "BLOCKED" : "APPROVED"}
                  </b>
                  <div className="mt-1 text-muted">{m.reason}</div>
                  <div className="mt-1">{m.answer}</div>
                </div>
              </div>
            ))}
            <div ref={end} />
          </div>
          <div className="mt-2 flex flex-wrap gap-2">
            {SAFE.slice(0, 2).map((s) => (
              <button key={s} className="rounded-full border border-border px-3 py-1 text-xs" onClick={() => send(s)}>
                {s.slice(0, 42)}…
              </button>
            ))}
          </div>
          <div className="mt-3 flex gap-2">
            <input
              className="min-h-11 flex-1 rounded-lg border border-border bg-surface-2 px-3 text-sm"
              value={text}
              onChange={(e) => setText(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && send()}
              placeholder="Ask…"
            />
            <Btn variant="primary" onClick={() => send()}>
              Send
            </Btn>
          </div>
          <div className="mt-2 flex gap-2">
            <Btn onClick={() => send(SAFE[Math.floor(Math.random() * SAFE.length)])}>Safe example</Btn>
            <Btn onClick={() => send(RISKY[Math.floor(Math.random() * RISKY.length)])}>Blocked example</Btn>
          </div>
        </Card>
        <div className="space-y-3">
          <Card>
            <div className="text-xs text-muted">Session risk</div>
            <div className={cn("num text-2xl", sessionRisk === "HIGH" ? "text-danger" : "text-ok")}>{sessionRisk}</div>
          </Card>
          <Card>
            <div className="text-xs text-muted">Last query ε cost</div>
            <div className="num font-mono text-xl">{last ? last.epsCost.toFixed(2) : "0.00"}</div>
          </Card>
          <Card>
            <div className="text-xs text-muted">Remaining budget (sum)</div>
            <div className="num text-xl">{budget.toFixed(2)} ε</div>
          </Card>
          <Card>
            <h3 className="text-xs font-bold tracking-wide text-muted uppercase">Decision pipeline</h3>
            {last ? (
              <div className="mt-3 flex flex-wrap gap-1 text-[11px]">
                {["REQUEST", "IDENTIFIER", "RISK", "POLICY", "BUDGET"].map((s) => (
                  <Tag key={s} tone={last.decision === "BLOCKED" && s !== "REQUEST" ? "danger" : "ok"}>
                    {s}
                  </Tag>
                ))}
                <Tag tone={last.decision === "BLOCKED" ? "danger" : "ok"}>{last.decision}</Tag>
              </div>
            ) : (
              <p className="mt-2 text-sm text-muted">Request → identifier check → risk → policy → budget → decision</p>
            )}
          </Card>
        </div>
      </div>
    </div>
  );
}
