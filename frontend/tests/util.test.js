import test from "node:test";
import assert from "node:assert/strict";
import { debounce, formatTime } from "../js/util.js";

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

test("debounce forwards arguments to the wrapped function", async () => {
  const seen = [];
  const fn = debounce((value) => seen.push(value), 10);
  fn("only");
  await new Promise((resolve) => setTimeout(resolve, 30));
  assert.deepEqual(seen, ["only"]);
});
