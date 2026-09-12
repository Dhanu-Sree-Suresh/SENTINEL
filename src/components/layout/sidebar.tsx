import { Link, useRouterState } from "@tanstack/react-router";
import {
  Activity,
  BookOpen,
  Bug,
  Cpu,
  Gauge,
  GitBranch,
  HeartPulse,
  LayoutDashboard,
  LineChart,
  ListChecks,
  MessageSquare,
  Radar,
  Scale,
  Server,
  Shield,
  ShieldAlert,
  Split,
  Workflow,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useApp } from "@/lib/store";

const GROUPS = [
  {
    label: "Command",
    items: [
      { to: "/", icon: LayoutDashboard, label: "Dashboard" },
      { to: "/overview", icon: GitBranch, label: "Overview" },
      { to: "/guided", icon: BookOpen, label: "Guided demo" },
    ],
  },
  {
    label: "Analytics & ML",
    items: [
      { to: "/prevalence", icon: LineChart, label: "Population prevalence" },
      { to: "/federated", icon: Cpu, label: "Federated + DP-SGD" },
      { to: "/ml", icon: Gauge, label: "ML laboratory" },
      { to: "/pipeline", icon: Workflow, label: "Secure pipeline" },
      { to: "/tradeoff", icon: Scale, label: "Privacy / utility" },
    ],
  },
  {
    label: "Access",
    items: [
      { to: "/console", icon: MessageSquare, label: "Analyst console" },
      { to: "/decisions", icon: ListChecks, label: "Access decisions" },
      { to: "/monitor", icon: Radar, label: "Live monitor" },
      { to: "/ledger", icon: Activity, label: "Privacy ledger" },
    ],
  },
  {
    label: "Security",
    items: [
      { to: "/attacklab", icon: Bug, label: "Attack lab" },
      { to: "/threat", icon: ShieldAlert, label: "Posture / kill-chain" },
      { to: "/differencing", icon: Split, label: "Differencing" },
      { to: "/policy", icon: Shield, label: "Policy" },
    ],
  },
  {
    label: "Ops",
    items: [
      { to: "/infrastructure", icon: Server, label: "Entities" },
      { to: "/health", icon: HeartPulse, label: "System health" },
      { to: "/audit", icon: ListChecks, label: "Audit" },
    ],
  },
];

export function Sidebar({ onNavigate }: { onNavigate?: () => void }) {
  const pathname = useRouterState({ select: (s) => s.location.pathname });
  const n = useApp((s) => s.entities.filter((e) => e.connected).length);

  return (
    <aside className="flex h-full flex-col border-r border-border bg-surface/95 backdrop-blur">
      <div className="flex items-center gap-3 border-b border-border px-4 py-4">
        <div className="flex size-10 items-center justify-center rounded-lg bg-accent/15 font-mono text-xs font-bold text-accent">
          SK
        </div>
        <div>
          <div className="text-sm font-semibold tracking-wide">SENTINEL</div>
          <div className="text-[10px] text-muted">PPA-GOV control plane</div>
        </div>
      </div>
      <nav className="flex-1 overflow-y-auto px-2 py-3">
        {GROUPS.map((g) => (
          <div key={g.label} className="mb-4">
            <div className="px-3 pb-1 text-[9px] font-bold tracking-[0.18em] text-muted uppercase">
              {g.label}
            </div>
            {g.items.map((it) => {
              const active = pathname === it.to;
              const Icon = it.icon;
              return (
                <Link
                  key={it.to}
                  to={it.to}
                  onClick={onNavigate}
                  className={cn(
                    "mb-0.5 flex items-center gap-2 rounded-lg px-3 py-2 text-[13px] text-muted transition-colors hover:bg-surface-2 hover:text-fg",
                    active &&
                      "bg-accent/12 text-fg shadow-[inset_3px_0_0_var(--color-accent)]",
                  )}
                >
                  <Icon className="size-4 shrink-0" />
                  {it.label}
                </Link>
              );
            })}
          </div>
        ))}
      </nav>
      <div className="border-t border-border p-3 text-[10px] leading-relaxed text-muted">
        Raw records shared: <b className="text-ok">0</b>
        <br />
        Connected entities: <b className="text-fg">{n}</b>
        <br />
        Synthetic data only · ε accounted
      </div>
    </aside>
  );
}
