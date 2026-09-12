import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import { Btn, Card, PageHead, Tag } from "@/components/ui/primitives";
import { useApp } from "@/lib/store";
import { cn } from "@/lib/utils";

export const Route = createFileRoute("/pipeline")({ component: Pipeline });

const PROT = [
  ["Custodian boundary", "Records remain inside the establishment", "LOCAL"],
  ["Local computation", "Statistic or gradient computed on-site", "LOCAL"],
  ["Privacy protection", "Clip + Gaussian / Laplace limits influence", "PROTECTED"],
  ["Secure aggregation", "Only masked sums are combined", "PROTECTED"],
  ["Policy validation", "Release rules and risk controls", "CONTROL"],
  ["Analytics result", "Approved aggregate leaves the plane", "RELEASE"],
];
const NAIVE = [
  ["Custodian boundary", "Records leave the establishment", "RISK"],
  ["Raw transfer", "Personal rows move to a central point", "RISK"],
  ["Central database", "A single exposure point is created", "RISK"],
  ["Analytics", "Exact results can reveal membership", "RISK"],
  ["Result", "Attacker receives precise output", "EXPOSED"],
];

function Pipeline() {
  const [mode, setMode] = useState<"protected" | "naive">("protected");
  const [i, setI] = useState(0);
  const log = useApp((s) => s.log);
  const arr = mode === "naive" ? NAIVE : PROT;
  const row = arr[i];

  return (
    <div>
      <PageHead
        kicker="End-to-end"
        title="Secure analytics pipeline"
        lead="Click a stage. Toggle naïve vs protected to see where exposure is created or prevented."
        extra={
          <div className="flex gap-2">
            <Btn
              variant="primary"
              onClick={() => {
                setMode("protected");
                setI(0);
                log("Pipeline", "Protected flow", "INFO");
              }}
            >
              Protected
            </Btn>
            <Btn
              variant="danger"
              onClick={() => {
                setMode("naive");
                setI(0);
                log("Pipeline", "Naïve raw-data flow", "HIGH");
              }}
            >
              Naïve
            </Btn>
          </div>
        }
      />
      <div className="grid gap-2">
        {arr.map((x, idx) => (
          <button
            key={x[0]}
            onClick={() => setI(idx)}
            className={cn(
              "rounded-xl border p-3 text-left",
              i === idx ? "border-accent bg-accent/10" : "border-border bg-surface",
            )}
          >
            <div className="flex items-center justify-between">
              <b>
                {idx + 1}. {x[0]}
              </b>
              <Tag tone={x[2] === "RISK" || x[2] === "EXPOSED" ? "danger" : "ok"}>{x[2]}</Tag>
            </div>
            <p className="text-sm text-muted">{x[1]}</p>
          </button>
        ))}
      </div>
      <Card className="mt-4">
        <h3 className="text-lg font-semibold">{row[0]}</h3>
        <p className="mt-1 text-sm text-muted">{row[1]}.</p>
      </Card>
    </div>
  );
}
