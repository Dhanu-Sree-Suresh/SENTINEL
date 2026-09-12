# SENTINEL · PPA-GOV

Privacy-preserving analytics control plane for sensitive government data.

SENTINEL lets multiple agencies obtain useful population analytics and a shared insider-threat model **without pooling raw records**. Each silo keeps its data local. Only clipped, noised, optionally masked updates and differentially private aggregates leave the entity.

This repository is the unified competition prototype. It merges:

| Source | What was kept |
|---|---|
| **ppa-gov-final-competition-ready** | Multi-page control-plane IA, analyst console, guided demo, policy/ledger |
| **ppa-gov-ctf2026-final-v4** | Dark command-center look (pink / cyan), page set, interactive charts |
| **sentinel-kill-chain** | Light SOC theme, kill-chain telemetry, measured FL / DP-SGD / attack numbers |
| **AEGIS prototype** | Live monitor, security posture, attack-lab pipeline, architecture diagram |
| **PPGA** | Guided workflow, prevalence / trade-off views |

All headline numbers are from an executed experiment (`public/results.json`), not placeholders.

---

## What it demonstrates

- **Multi-entity collaboration** — five synthetic government silos, ~32,000 records, ~4% positive rate, non-IID
- **Federated learning + DP-SGD** — local training, clip \(C=1.5\), Gaussian noise, Rényi-DP accountant, secure aggregation
- **Concrete ML task** — binary insider-threat risk classification (logistic regression backbone + model-family comparison)
- **Naïve vs protected** — pooled training vs FL+DP at $\varepsilon \approx 4$
- **Privacy / utility trade-off** — $\varepsilon$ sweep from 0.5 to 32
- **Controlled attacks** — membership inference, gradient inversion, differencing, rare-subgroup reconstruction, repeated queries, poisoning
- **SOC operations** — live monitor, kill-chain stages, health, audit, analyst chat console
- **Dual theme** — dark PPA-GOV control plane and light Sentinel SOC

### Headline measured results

| Setting | ROC-AUC | Notes |
|---|---|---|
| Naïve pooled (logistic) | **0.597** | Utility ceiling; gradients fully exposed |
| Federated, no DP | 0.592 | No raw rows moved |
| Federated + DP-SGD \(\varepsilon \approx 4\) | **0.594** | Utility essentially held |
| Gradient inversion (raw) | cosine \(\approx 1.0\) | Reconstructs the batch |
| Gradient inversion (DP) | cosine \(\approx 0.0003\) | Collapses |
| Membership inference (naïve) | AUC 0.510 | Weak-signal task; reported honestly |
| Membership inference (FL+DP) | AUC 0.491 | Near chance |

---

## Quick start

### Prerequisites

- **Node.js 22+** and npm
- Optional, only to re-run the research engine: **Python 3.11+**

### Install

```bash
npm install
```

### Start

```bash
npm run dev
```

Opens the app at **http://localhost:8080**.

The first load is the SOC dashboard. Use the sidebar to move between pages, the sun/moon control to switch light/dark, and the **Guided demo** button (bottom-right) for an eight-step walkthrough.

### Production build

```bash
npm run build
```

### Preview the production build

```bash
npm run preview
```

### Typecheck / lint / tests

```bash
npm run typecheck
npm run lint
npm test
```

---

## Commands

| Command | What it does |
|---|---|
| `npm install` | Install JavaScript dependencies |
| `npm run dev` | Start the interactive app on **port 8080** (`0.0.0.0`) |
| `npm run build` | Production build (Vite + Nitro / Vercel preset) |
| `npm run preview` | Serve the production build (loopback, port 8081) |
| `npm run typecheck` | TypeScript `tsc --noEmit` |
| `npm test` | Node test runner (scripts + lib tests) |
| `npm run lint` | ESLint |
| `npm run format` | Prettier write |

Default **start command:** `npm run dev`  
Default **build command:** `npm run build`  
Default **install command:** `npm install`  
Dev server **port:** `8080`

---

## Deploying to Render

| Setting | Value |
|---|---|
| Environment | Node |
| Build command | `npm install && npm run build` |
| Start command | `npm start` (runs `node .output/server/index.mjs`) |
| Node version | 22 (pinned by `.node-version`) |
| Port | Render sets `PORT` automatically — Nitro's Node server reads it, no config needed |
| Health check path | `/` |

A `render.yaml` Blueprint is included — connect the repo and Render will pick up the build/start commands and Node version automatically.

Notes:
- `DATABASE_URL` is optional. Unset, the app runs on an embedded in-memory Postgres (PGLite) that resets on every restart/deploy. Set it (Render Postgres, Neon, etc.) to persist data.
- Auth is off by default in this prototype, so no auth secrets are required to deploy.
- The production build uses Nitro's default Node server output (`.output/server/index.mjs`), which is portable across Render, Railway, Docker, or a bare VM — not tied to Vercel's serverless format.

**"Blocked request... add to server.allowedHosts" on the live site:** this means Render is actually running the Vite *dev* server (`npm run dev` / `start:dev`) instead of the built production server. If your Render Web Service was created before this Start Command was set, Render keeps whatever Start Command you configured manually and does not retroactively read `render.yaml`. Fix: in the Render dashboard, open the service → **Settings** → **Start Command**, set it to `npm start` (or `node .output/server/index.mjs`), save, then **Manual Deploy → Clear build cache & deploy**.

---

## Application map

### Command
| Route | Page | Purpose |
|---|---|---|
| `/` | Dashboard | SOC KPIs, kill-chain, evidence, interactive charts |
| `/overview` | Overview | Five-entity collaboration picture |
| `/guided` | Guided demo | Jury walkthrough |

### Analytics & ML
| Route | Page | Purpose |
|---|---|---|
| `/prevalence` | Population prevalence | Protected aggregates, no raw rows |
| `/federated` | Federated + DP-SGD | Round controls, stats, clickable architecture |
| `/ml` | ML laboratory | Task, model families, DP-SGD recipe |
| `/pipeline` | Secure pipeline | Data → local train → SecAgg → global model |
| `/tradeoff` | Privacy / utility | $\varepsilon$ sweep, attack confidence vs utility |

### Access
| Route | Page | Purpose |
|---|---|---|
| `/console` | Analyst console | Chat queries; individual-level asks are blocked |
| `/decisions` | Access decisions | ALLOWED / BLOCKED log |
| `/monitor` | Live monitor | Streaming FL / SecAgg / kill-chain events |
| `/ledger` | Privacy ledger | $\varepsilon$ spend per entity |

### Security
| Route | Page | Purpose |
|---|---|---|
| `/attacklab` | Attack lab | Run MI / GI / poisoning / differencing (naïve vs protected) |
| `/threat` | Posture / kill-chain | AEGIS-style posture + SENTINEL stages |
| `/differencing` | Differencing | Composition / overlapping-query risk |
| `/policy` | Policy | What the analyst is allowed to ask |

### Ops
| Route | Page | Purpose |
|---|---|---|
| `/infrastructure` | Entities | Connect / disconnect silos, remaining budget |
| `/health` | System health | Aggregator, DP engine, policy, audit vitality |
| `/audit` | Audit | Operator trail of queries, attacks, rounds |

---

## Architecture

```
Entity A..E  ── local records stay here ──► DP-SGD (clip + noise)
        │                                         │
        │     only updates / DP answers           ▼
        └──────────────►  Secure aggregator  ──► global model
                              │
                     query monitor + kill-chain
                     policy gate + ε accountant
                              │
                         analyst console
```

**Hard rule:** raw personal records are never uploaded. The dashboard, console, and attack lab operate on aggregates, model updates, and synthetic telemetry.

State lives in a Zustand store (`src/lib/store.ts`) with a privacy engine (`src/lib/engine.ts`) that classifies queries, answers aggregates, and scores attacks against the measured experiment (`src/lib/results.ts` / `public/results.json`).

---

## Tech stack

- React 19 + TypeScript
- TanStack Start / Router / Query
- Vite 8, Tailwind CSS v4
- Zustand, Recharts, Zod, Lucide
- Optional: Python research engine under `research/` (federated DP-SGD, attacks, tests)

---

## Project layout

```
.
├── README.md                 ← this file
├── package.json
├── vite.config.ts            ← dev server: 0.0.0.0:8080
├── tsconfig.json
├── startup.sh                ← idempotent preview start
├── public/
│   ├── results.json          ← executed experiment output
│   ├── favicon.svg
│   └── og.jpg
├── src/
│   ├── components/           ← shell, sidebar, charts, primitives
│   ├── lib/
│   │   ├── engine.ts         ← query policy + attack scoring
│   │   ├── results.ts        ← measured metrics
│   │   └── store.ts          ← app state (entities, live feed, chat)
│   ├── routes/               ← one file per page
│   ├── styles.css
│   └── router.tsx
└── research/                 ← optional Python experiment engine
    ├── src/                  ← FL, DP-SGD, attacks, kill-chain
    ├── experiments/
    ├── tests/
    └── requirements.txt
```

---

## Re-running the research engine

The UI already ships with measured numbers. To regenerate them:

```bash
cd research
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python experiments/run_experiment.py
```

Copy the resulting `results.json` into `public/results.json` (and, if you change constants, `src/lib/results.ts`).

---

## Features

1. **Dashboard** — KPIs, kill-chain, naïve vs DP charts. Toggle light/dark.
2. **ML laboratory** — task definition and model-family comparison.
3. **Attack lab** — run *Gradient inversion* naïve vs protected; then membership inference.
4. **Federated + DP-SGD** — click architecture stages; run a training round.
5. **Analyst console** — ask a prevalence question (allowed); ask for a named patient (blocked).
6. **Live monitor + health + audit** — confirm the trail is populated, not empty.
7. **Trade-off** — $\varepsilon$ vs utility vs attack confidence.

---

## Honest limitations

- Synthetic data only. No real personal records are processed.
- Membership-inference advantage is modest even in the naïve setting because the classification signal is weak; that is reported, not hidden.
- Secure aggregation is a protocol simulation (mask exchange / drop handling), not a production MPC deployment.
- Auth is off. This is a demonstration control plane, not a multi-tenant production service.

---

## License / use

Competition prototype for privacy-preserving analytics on sensitive government data. Synthetic data and measured results only. Not for production processing of real personal information.
