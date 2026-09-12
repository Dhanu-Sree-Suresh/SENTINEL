import { createFileRoute } from "@tanstack/react-router";
import { Card, PageHead } from "@/components/ui/primitives";
import { useApp } from "@/lib/store";

export const Route = createFileRoute("/decisions")({ component: Decisions });

function Decisions() {
  const q = useApp((s) => s.queries);
  return (
    <div>
      <PageHead
        kicker="Auditible"
        title="Access decision center"
        lead="Every analyst request is classified and logged with a plain-language reason."
      />
      <div className="grid gap-3 sm:grid-cols-3">
        <Card>
          <div className="text-xs text-muted">Allowed</div>
          <div className="num text-3xl text-ok">{q.filter((x) => x.decision === "ALLOWED").length}</div>
        </Card>
        <Card>
          <div className="text-xs text-muted">Blocked</div>
          <div className="num text-3xl text-danger">{q.filter((x) => x.decision === "BLOCKED").length}</div>
        </Card>
        <Card>
          <div className="text-xs text-muted">Medium risk</div>
          <div className="num text-3xl text-warn">{q.filter((x) => x.risk === "MEDIUM").length}</div>
        </Card>
      </div>
      <Card className="mt-4 overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-[11px] text-muted">
              <th className="py-2">Time</th>
              <th>Request</th>
              <th>Decision</th>
              <th>Risk</th>
              <th>Why</th>
            </tr>
          </thead>
          <tbody>
            {q
              .slice()
              .reverse()
              .map((x) => (
                <tr key={x.id} className="border-t border-border">
                  <td className="py-2">{new Date(x.ts).toLocaleTimeString()}</td>
                  <td className="max-w-[240px] truncate">{x.q}</td>
                  <td className={x.decision === "BLOCKED" ? "text-danger" : "text-ok"}>{x.decision}</td>
                  <td>{x.risk}</td>
                  <td className="max-w-[280px] text-muted">{x.reason}</td>
                </tr>
              ))}
            {q.length === 0 ? (
              <tr>
                <td colSpan={5} className="py-6 text-muted">
                  No decisions yet. Use the Analyst Console.
                </td>
              </tr>
            ) : null}
          </tbody>
        </table>
      </Card>
    </div>
  );
}
