import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import { Btn, Card, Field, Input, PageHead, Tag } from "@/components/ui/primitives";
import { useApp } from "@/lib/store";

export const Route = createFileRoute("/differencing")({ component: Diff });

function Diff() {
  const [pop, setPop] = useState(500);
  const [q1, setQ1] = useState("Region = Dubai");
  const [q2, setQ2] = useState("Condition = Diabetes");
  const [q3, setQ3] = useState("Age = 40–45");
  const [final, setFinal] = useState<number | null>(null);
  const log = useApp((s) => s.log);
  const vals = [q1, q2, q3].filter(Boolean);
  const remaining = vals.map((_, i) => Math.max(1, Math.round(pop * Math.pow(0.42, i + 1))));

  function analyze() {
    const f = remaining[remaining.length - 1] ?? pop;
    setFinal(f);
    log("Differencing analysis", vals.join(" → "), f <= 5 ? "HIGH" : "INFO");
  }

  const risk = final == null ? null : final <= 5 ? "HIGH" : final <= 20 ? "MEDIUM" : "LOW";

  return (
    <div>
      <PageHead
        kicker="Attack surface"
        title="Differencing detector"
        lead="Build a sequence of related filters. If the implied remaining population is too small, the release should be blocked."
      />
      <Card>
        <div className="grid gap-3 sm:grid-cols-3">
          <Field label="Starting population">
            <Input type="number" min={2} value={pop} onChange={(e) => setPop(+e.target.value || 2)} />
          </Field>
          <Field label="Filter 1">
            <Input value={q1} onChange={(e) => setQ1(e.target.value)} />
          </Field>
          <Field label="Filter 2">
            <Input value={q2} onChange={(e) => setQ2(e.target.value)} />
          </Field>
          <Field label="Filter 3">
            <Input value={q3} onChange={(e) => setQ3(e.target.value)} />
          </Field>
        </div>
        <div className="mt-3 flex gap-2">
          <Btn variant="primary" onClick={analyze}>
            Analyze sequence
          </Btn>
        </div>
        <div className="mt-4 space-y-2">
          {vals.map((v, i) => (
            <div key={v} className="flex justify-between rounded-lg border border-border px-3 py-2 text-sm">
              <span>
                Q{i + 1}: {v}
              </span>
              <span className="text-muted">remaining ≈ {remaining[i]}</span>
            </div>
          ))}
        </div>
        {final != null && risk ? (
          <div className="mt-4">
            <Tag tone={risk === "HIGH" ? "danger" : risk === "MEDIUM" ? "warn" : "ok"}>{risk} differencing risk</Tag>
            <p className="mt-2 text-sm text-muted">
              Modeled remaining population is <b>{final}</b>.{" "}
              {risk === "HIGH"
                ? "Too selective — block or generalize the final release."
                : "Sequence remains sufficiently broad for this check."}
            </p>
          </div>
        ) : null}
      </Card>
    </div>
  );
}
