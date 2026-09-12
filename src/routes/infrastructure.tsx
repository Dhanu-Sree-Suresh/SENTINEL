import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import { Btn, Card, Field, Input, PageHead, Select, Tag } from "@/components/ui/primitives";
import { useApp } from "@/lib/store";

export const Route = createFileRoute("/infrastructure")({ component: Infra });

function Infra() {
  const entities = useApp((s) => s.entities);
  const add = useApp((s) => s.addEntity);
  const [name, setName] = useState("");
  const [records, setRecords] = useState(4000);
  const [connected, setConnected] = useState("yes");
  const [msg, setMsg] = useState("");

  return (
    <div>
      <PageHead
        kicker="Silos"
        title="Entity registry"
        lead="Five synthetic government-style custodians. Add another establishment without ever uploading real PII."
      />
      <Card>
        <div className="grid gap-3 sm:grid-cols-3">
          <Field label="Name">
            <Input value={name} onChange={(e) => setName(e.target.value)} placeholder="Entity F · Customs" />
          </Field>
          <Field label="Records">
            <Input type="number" min={0} value={records} onChange={(e) => setRecords(+e.target.value || 0)} />
          </Field>
          <Field label="Link">
            <Select value={connected} onChange={(e) => setConnected(e.target.value)}>
              <option value="yes">Connect immediately</option>
              <option value="no">Keep offline</option>
            </Select>
          </Field>
        </div>
        <Btn
          variant="primary"
          className="mt-3"
          onClick={() => {
            if (!name.trim() || !records) {
              setMsg("Enter a name and record count.");
              return;
            }
            add({ name: name.trim(), records, connected: connected === "yes" });
            setMsg(`Added ${name.trim()}.`);
            setName("");
          }}
        >
          Add entity
        </Btn>
        {msg ? <p className="mt-2 text-sm text-ok">{msg}</p> : null}
      </Card>
      <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {entities.map((e) => (
          <Card key={e.id}>
            <div className="flex justify-between">
              <h3 className="font-semibold">{e.name}</h3>
              <Tag tone={e.connected ? "ok" : "warn"}>{e.connected ? "connected" : "offline"}</Tag>
            </div>
            <div className="num mt-2 text-2xl">{e.records.toLocaleString()}</div>
            <p className="text-xs text-muted">Local privacy engine · raw rows remain local</p>
          </Card>
        ))}
      </div>
    </div>
  );
}
