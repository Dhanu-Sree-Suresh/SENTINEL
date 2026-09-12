import { createFileRoute } from "@tanstack/react-router";
import { useMemo, useState } from "react";
import { Btn, Card, Field, PageHead, Select, Tag } from "@/components/ui/primitives";
import { useApp } from "@/lib/store";
import { seeded } from "@/lib/utils";

export const Route = createFileRoute("/prevalence")({ component: Prevalence });

const RATES: Record<string, number> = {
  Diabetes: 8.7,
  Hypertension: 16.2,
  Asthma: 5.8,
  "Cardiovascular disease": 11.4,
  "Insider-threat flag": 4.06,
};
const REG: Record<string, number> = {
  Dubai: 1,
  "Abu Dhabi": 1.08,
  Sharjah: 0.94,
  Ajman: 0.91,
  "Ras Al Khaimah": 1.02,
};

function Prevalence() {
  const entities = useApp((s) => s.entities);
  const eps = useApp((s) => s.eps);
  const log = useApp((s) => s.log);
  const [region, setRegion] = useState("Dubai");
  const [site, setSite] = useState("all");
  const [cond, setCond] = useState("Diabetes");
  const connected = entities.filter((e) => e.connected);

  const rec = site === "all" ? connected.reduce((a, e) => a + e.records, 0) : Number(entities.find((e) => e.id === site)?.records || 0);
  const noise = 0.25 / Math.max(0.05, eps);
  const seed = (region.length + cond.length + rec) % 7;
  const val = Math.max(0.1, Math.min(45, (RATES[cond] || 8) * (REG[region] || 1) + (seed - 3) * noise));
  const count = Math.max(0, Math.round((rec * val) / 100));

  const dots = useMemo(() => {
    const rnd = seeded(rec + cond.length * 9);
    const n = Math.min(70, Math.max(18, Math.round(rec / 500)));
    return Array.from({ length: n }, () => ({ x: 3 + rnd() * 92, y: 12 + rnd() * 76, o: 0.3 + rnd() * 0.4 }));
  }, [rec, cond, region]);

  return (
    <div>
      <PageHead
        kicker="Statistic"
        title="Protected population prevalence"
        lead="Laplace-calibrated aggregate. Change region, entity and condition — only a noisy rate is released."
      />
      <div className="grid gap-3 sm:grid-cols-3">
        <Card>
          <div className="text-xs text-muted">Protected prevalence</div>
          <div className="num text-3xl">{val.toFixed(1)}%</div>
        </Card>
        <Card>
          <div className="text-xs text-muted">Protected count equivalent</div>
          <div className="num text-3xl">≈ {count.toLocaleString()}</div>
        </Card>
        <Card>
          <div className="text-xs text-muted">Uncertainty</div>
          <div className="num text-3xl text-warn">± {noise.toFixed(2)} pp</div>
          <Tag tone="ok">raw records shared: 0</Tag>
        </Card>
      </div>
      <Card className="mt-4">
        <div className="grid gap-3 sm:grid-cols-3">
          <Field label="Region">
            <Select value={region} onChange={(e) => setRegion(e.target.value)}>
              {Object.keys(REG).map((r) => (
                <option key={r}>{r}</option>
              ))}
            </Select>
          </Field>
          <Field label="Establishment">
            <Select value={site} onChange={(e) => setSite(e.target.value)}>
              <option value="all">All connected</option>
              {connected.map((e) => (
                <option key={e.id} value={e.id}>
                  {e.name}
                </option>
              ))}
            </Select>
          </Field>
          <Field label="Condition">
            <Select value={cond} onChange={(e) => setCond(e.target.value)}>
              {Object.keys(RATES).map((r) => (
                <option key={r}>{r}</option>
              ))}
            </Select>
          </Field>
        </div>
        <Btn
          variant="primary"
          className="mt-3"
          onClick={() => log("Protected prevalence", `${cond} · ${region}`, "INFO")}
        >
          Compute protected result
        </Btn>
        <div className="relative mt-4 h-44 overflow-hidden rounded-lg border border-border bg-surface-2">
          {dots.map((d, i) => (
            <i key={i} className="absolute size-2 rounded-full bg-accent-2" style={{ left: `${d.x}%`, top: `${d.y}%`, opacity: d.o }} />
          ))}
        </div>
        <p className="mt-3 text-sm text-muted">
          {cond} in {region} estimated at <b>{val.toFixed(1)}%</b> from {rec.toLocaleString()} contributing records. Privacy cost 0.05 ε.
        </p>
      </Card>
    </div>
  );
}
