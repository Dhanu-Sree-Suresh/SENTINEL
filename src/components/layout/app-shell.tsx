import { useEffect, useState, type ReactNode } from "react";
import { Moon, Sun, Menu, X } from "lucide-react";
import { Sidebar } from "./sidebar";
import { useApp, nextLiveTick } from "@/lib/store";
import { Tag } from "@/components/ui/primitives";
import { GuideFab } from "@/components/layout/guide-fab";

export function AppShell({ children }: { children: ReactNode }) {
  const theme = useApp((s) => s.theme);
  const setTheme = useApp((s) => s.setTheme);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    document.documentElement.classList.toggle("dark", theme === "dark");
    document.documentElement.classList.toggle("light", theme === "light");
  }, [theme]);

  useEffect(() => {
    const t = setInterval(() => nextLiveTick(), 3500);
    nextLiveTick();
    return () => clearInterval(t);
  }, []);

  return (
    <div className="relative min-h-screen text-fg">
      <div className="grid-overlay" />
      <div className="relative z-[1] flex min-h-screen">
        <div
          className={`z-40 w-[270px] shrink-0 ${
            open
              ? "fixed inset-y-0 left-0 min-h-screen"
              : "hidden min-h-screen lg:static lg:block"
          }`}
        >
          <Sidebar onNavigate={() => setOpen(false)} />
        </div>
        {open ? (
          <button
            className="fixed inset-0 z-30 bg-black/50 lg:hidden"
            aria-label="Close menu"
            onClick={() => setOpen(false)}
          />
        ) : null}
        <div className="flex min-h-screen min-w-0 flex-1 flex-col">
          <header className="sticky top-0 z-20 flex h-16 items-center justify-between border-b border-border bg-bg/80 px-4 backdrop-blur">
            <div className="flex items-center gap-2">
              <button
                className="inline-flex size-11 items-center justify-center rounded-lg border border-border lg:hidden"
                onClick={() => setOpen((v) => !v)}
                aria-label="Menu"
              >
                {open ? <X className="size-4" /> : <Menu className="size-4" />}
              </button>
              <span className="text-xs tracking-wide text-muted uppercase">
                SENTINEL / PPA-GOV
              </span>
            </div>
            <div className="flex items-center gap-2">
              <Tag tone="ok">Privacy active</Tag>
              <Tag>Raw data local</Tag>
              <button
                className="inline-flex size-11 items-center justify-center rounded-lg border border-border bg-surface-2"
                onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
                aria-label="Toggle theme"
                title={
                  theme === "dark"
                    ? "Switch to Sentinel light SOC"
                    : "Switch to dark control plane"
                }
              >
                {theme === "dark" ? <Sun className="size-4" /> : <Moon className="size-4" />}
              </button>
            </div>
          </header>
          <main className="mx-auto w-full max-w-[1280px] flex-1 px-4 py-6 sm:px-6">{children}</main>
        </div>
      </div>
      <GuideFab />
    </div>
  );
}
