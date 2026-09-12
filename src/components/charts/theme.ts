import { useApp } from "@/lib/store";

export function useChartColors() {
  const theme = useApp((s) => s.theme);
  if (theme === "light") {
    return {
      fg: "#1c2b30",
      muted: "#5b6b74",
      accent: "#1a8a72",
      accent2: "#3d6f99",
      ok: "#2e8b6f",
      warn: "#c48412",
      danger: "#c45c50",
      grid: "#d7dee1",
    };
  }
  return {
    fg: "#f4f4f7",
    muted: "#8b93a7",
    accent: "#ff4fb3",
    accent2: "#6fd9ff",
    ok: "#44d39a",
    warn: "#f4bd54",
    danger: "#ff5f78",
    grid: "#252a3a",
  };
}
