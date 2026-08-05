import test from "node:test";
import assert from "node:assert/strict";
import { debounce, formatTime } from "../js/util.js";
import { SettingsPanel } from "../js/settings.js";

test("formatTime formats minutes and seconds", () => {
  assert.equal(formatTime(0), "00:00");
  assert.equal(formatTime(59), "00:59");
  assert.equal(formatTime(60), "01:00");
  assert.equal(formatTime(125.5), "02:05");
  assert.equal(formatTime(3661), "61:01");
});

test("debounce fires once after the trailing delay", async () => {
  let calls = 0;
  const fn = debounce(() => calls++, 10);
  fn();
  fn();
  fn();
  await new Promise((resolve) => setTimeout(resolve, 30));
  assert.equal(calls, 1);
});

test("settings panel saves numeric playback settings and waits for a media scan", async () => {
  const listeners = {};
  const field = (value = "") => ({ value, checked: false });
  const elements = {
    dialog: { showModal() {}, close() {} },
    form: { addEventListener(type, callback) { listeners[type] = callback; } },
    closeButton: { addEventListener() {} },
    error: { hidden: true, textContent: "" },
    status: { hidden: true, textContent: "" },
    fields: {
      theme: field("dark"), volume: field("25"), speed: field("1.25"), subtitles: field(),
      reduceMotion: field(), welcome: field("always"), teacherKey: field("KeyT"),
      readingPage: field("/reading.html"), mediaRoot: field("custom"),
      currentPassword: field(), newPassword: field(),
    },
  };
  elements.fields.subtitles.checked = true;
  const calls = [];
  const panel = new SettingsPanel(elements, {
    api: {
      async saveSettings(values) { calls.push(["settings", values]); },
      async config(root) { calls.push(["config", root]); return { scan: { status: "scanning" } }; },
    },
    onSaved() { calls.push(["saved"]); },
    async onScan(scan) { calls.push(["scan", scan.status]); },
  });
  await panel.save();
  assert.equal(calls[0][0], "settings");
  assert.equal(calls[0][1].default_volume, 25);
  assert.equal(calls[0][1].default_speed, 1.25);
  assert.deepEqual(calls.slice(1), [["config", "custom"], ["scan", "scanning"], ["saved"]]);
});

test("debounce forwards arguments to the wrapped function", async () => {
  const seen = [];
  const fn = debounce((value) => seen.push(value), 10);
  fn("only");
  await new Promise((resolve) => setTimeout(resolve, 30));
  assert.deepEqual(seen, ["only"]);
});
