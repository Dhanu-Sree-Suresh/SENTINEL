import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function fmt(n: number | null | undefined, d = 3) {
  if (n == null || Number.isNaN(n)) return "—";
  return n.toFixed(d);
}

export function fmtPct(n: number, d = 1) {
  return `${n.toFixed(d)}%`;
}

export function nowId() {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
}

export function seedHash(s: string) {
  let h = 2166136261;
  for (let i = 0; i < s.length; i++) {
    h ^= s.charCodeAt(i);
    h = Math.imul(h, 16777619);
  }
  return Math.abs(h);
}

export function seeded(seed: number) {
  let x = seed || 1;
  return () => {
    x ^= x << 13;
    x ^= x >>> 17;
    x ^= x << 5;
    return ((x >>> 0) % 10000) / 10000;
  };
}
