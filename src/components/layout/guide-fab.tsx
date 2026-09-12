import { useState } from "react";
import { useNavigate, useRouterState } from "@tanstack/react-router";
import { Btn } from "@/components/ui/primitives";

const STEPS: { title: string; body: string; to: string }[] = [
  { title: "Business problem", body: "Agencies hold sensitive records but cannot pool them under data-residency / PDPL constraints.", to: "/" },
  { title: "Entities", body: "Five silos keep raw data local. Only updates or DP answers leave the entity.", to: "/overview" },
  { title: "Naïve baseline", body: "Centralized training on pooled data: ROC-AUC ≈ 0.60 — useful, but exposed.", to: "/ml" },
  { title: "Attack naïve", body: "Membership inference and gradient inversion against unprotected gradients.", to: "/attacklab" },
  { title: "Enable privacy", body: "Federated learning + DP-SGD (ε≈4) + secure aggregation.", to: "/federated" },
  { title: "Protected result", body: "Utility remains comparable; gradient inversion collapses.", to: "/tradeoff" },
  { title: "Live monitor", body: "Kill-chain telemetry and risk tiers as first-class SOC signal.", to: "/monitor" },
  { title: "Business value", body: "Shared intelligence without centralizing personal records.", to: "/audit" },
];

export function GuideFab() {
  const [open, setOpen] = useState(false);
  const [i, setI] = useState(0);
  const nav = useNavigate();
  const path = useRouterState({ select: (s) => s.location.pathname });

  function go(n: number) {
    const next = (n + STEPS.length) % STEPS.length;
    setI(next);
    if (STEPS[next].to !== path) nav({ to: STEPS[next].to });
  }

  return (
    <>
      <button
        className="fixed right-4 bottom-4 z-50 min-h-11 rounded-full bg-accent px-4 text-sm font-semibold text-white shadow-lg"
        onClick={() => setOpen(true)}
      >
        Guided demo
      </button>
      {open ? (
        <div className="fixed inset-0 z-50">
          <button className="absolute inset-0 bg-black/50" onClick={() => setOpen(false)} aria-label="Close" />
          <section className="absolute right-4 bottom-20 w-[min(420px,92vw)] rounded-xl border border-border bg-surface p-4 shadow-xl">
            <div className="text-[10px] font-bold tracking-[0.16em] text-accent uppercase">Guided demo</div>
            <h2 className="mt-1 text-lg font-semibold">{STEPS[i].title}</h2>
            <p className="mt-2 text-sm text-muted">{STEPS[i].body}</p>
            <div className="mt-4 flex items-center justify-between">
              <span className="text-xs text-muted">
                Step {i + 1} / {STEPS.length}
              </span>
              <div className="flex gap-2">
                <Btn onClick={() => go(i - 1)}>Previous</Btn>
                <Btn variant="primary" onClick={() => go(i + 1)}>
                  Next
                </Btn>
              </div>
            </div>
          </section>
        </div>
      ) : null}
    </>
  );
}
