import test from "node:test";
import assert from "node:assert/strict";
import { applyTheme, getThemeColor, normalizeTheme, THEMES } from "../js/themes.js";

test("themes expose the complete supported palette", () => {
  assert.deepEqual(Object.keys(THEMES), [
    "dark",
    "amoled",
    "nord",
    "tokyo-night",
    "catppuccin-mocha",
    "dracula",
    "gruvbox",
  ]);
  assert.equal(normalizeTheme("missing"), "dark");
  assert.equal(getThemeColor("nord"), "#2e3440");
});

test("applyTheme updates a supplied root immediately", () => {
  const root = { dataset: {}, setAttribute() {} };
  assert.equal(applyTheme("tokyo-night", root), "tokyo-night");
  assert.equal(root.dataset.theme, "tokyo-night");
});
