export const THEMES = Object.freeze({
  dark: "Hibiki Dark",
  amoled: "AMOLED",
  nord: "Nord",
  "tokyo-night": "Tokyo Night",
  "catppuccin-mocha": "Catppuccin Mocha",
  dracula: "Dracula",
  gruvbox: "Gruvbox",
});

export function normalizeTheme(value) {
  return Object.hasOwn(THEMES, value) ? value : "dark";
}

export function applyTheme(value, root = null) {
  const theme = normalizeTheme(value);
  const target = root || (typeof document !== "undefined" ? document.documentElement : null);
  if (target) {
    target.dataset.theme = theme;
    const meta = typeof document !== "undefined" ? document.querySelector("#theme-color") : null;
    if (meta) meta.setAttribute("content", getThemeColor(theme));
  }
  try { globalThis.localStorage?.setItem("hibiki.theme", theme); } catch { /* storage can be unavailable */ }
  return theme;
}

export function getThemeColor(value) {
  const colors = {
    dark: "#111111",
    amoled: "#000000",
    nord: "#2e3440",
    "tokyo-night": "#1a1b26",
    "catppuccin-mocha": "#1e1e2e",
    dracula: "#282a36",
    gruvbox: "#282828",
  };
  return colors[normalizeTheme(value)];
}
