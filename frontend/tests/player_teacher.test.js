import test, { afterEach } from "node:test";
import assert from "node:assert/strict";
import { Player } from "../js/player.js";
import { TeacherMode } from "../js/teacher.js";

class FakeElement {
  constructor() {
    this.listeners = {};
    this.children = [];
    this.options = [];
    this.attributes = {};
    this.hidden = false;
    this.classList = {
      values: new Set(),
      add: (value) => this.classList.values.add(value),
      remove: (value) => this.classList.values.delete(value),
    };
    this.value = "";
    this.paused = true;
    this.currentTime = 0;
    this.duration = 0;
    this.volume = 1;
    this.playbackRate = 1;
    this.textTracks = [];
    this.audioTracks = undefined;
  }

  addEventListener(type, callback) {
    (this.listeners[type] ||= []).push(callback);
  }

  dispatch(type, event = {}) {
    for (const callback of this.listeners[type] || []) callback({ target: this, ...event });
  }

  append(...children) {
    this.children.push(...children);
    for (const child of children) {
      if (child?.value !== undefined) this.options.push(child);
    }
  }

  replaceChildren(...children) {
    this.children = children;
    this.options = children.filter((child) => child?.value !== undefined);
  }

  querySelectorAll() { return []; }
  setAttribute(name, value) { this.attributes[name] = String(value); }
  removeAttribute(name) { delete this.attributes[name]; }
  getAttribute(name) { return this.attributes[name]; }
  matches() { return false; }
  focus() { this.focused = true; }
  load() {}
  play() { this.paused = false; return Promise.resolve(); }
  pause() { this.paused = true; }
}

const originalDocument = globalThis.document;
const originalOption = globalThis.Option;
const originalRequestAnimationFrame = globalThis.requestAnimationFrame;

function installDocument(playerShell = new FakeElement()) {
  const documentElement = new FakeElement();
  documentElement.fullscreenElement = null;
  documentElement.querySelector = () => playerShell;
  documentElement.createElement = () => new FakeElement();
  documentElement.addEventListener = () => {};
  globalThis.document = documentElement;
  globalThis.Option = function Option(label, value) { this.label = label; this.value = value; };
  globalThis.requestAnimationFrame = (callback) => callback();
  return documentElement;
}

afterEach(() => {
  globalThis.document = originalDocument;
  globalThis.Option = originalOption;
  globalThis.requestAnimationFrame = originalRequestAnimationFrame;
});

test("player applies zero volume and safe defaults without audioTracks support", () => {
  installDocument();
  const video = new FakeElement();
  const volume = new FakeElement();
  const speed = new FakeElement();
  speed.options = [{ value: "1" }, { value: "1.25" }];
  const player = new Player({
    video,
    empty: new FakeElement(),
    loading: new FakeElement(),
    error: new FakeElement(),
    playToggle: new FakeElement(),
    timeline: new FakeElement(),
    timeDisplay: new FakeElement(),
    muteToggle: new FakeElement(),
    volume,
    subtitle: new FakeElement(),
    audioTrack: new FakeElement(),
    speed,
    fullscreenToggle: new FakeElement(),
  });
  assert.doesNotThrow(() => player.refreshAudioTracks());
  player.applyDefaults({ volume: 0, speed: 1.25 });
  assert.equal(video.volume, 0);
  assert.equal(volume.value, "0");
  assert.equal(video.playbackRate, 1.25);
});

test("player starts loading immediately and supports prefixed fullscreen APIs", async () => {
  const documentElement = installDocument();
  const playerShell = documentElement.querySelector();
  let requested = false;
  playerShell.webkitRequestFullscreen = () => { requested = true; };
  const video = new FakeElement();
  const loading = new FakeElement();
  const player = new Player({
    video,
    empty: new FakeElement(),
    loading,
    error: new FakeElement(),
    playToggle: new FakeElement(),
    timeline: new FakeElement(),
    timeDisplay: new FakeElement(),
    muteToggle: new FakeElement(),
    volume: new FakeElement(),
    subtitle: new FakeElement(),
    audioTrack: new FakeElement(),
    speed: new FakeElement(),
    fullscreenToggle: new FakeElement(),
  });
  player.load({ url: "/video.mp4" }, { id: "episode" });
  assert.equal(loading.hidden, false);
  player.fullscreen();
  assert.equal(requested, true);
  await player.exitFullscreen();
});

test("player loads thumbnail and subtitle manifest and handles missing fullscreen API", () => {
  const documentElement = installDocument();
  const video = new FakeElement();
  const subtitle = new FakeElement();
  const fullscreen = new FakeElement();
  const player = new Player({
    video,
    empty: new FakeElement(),
    loading: new FakeElement(),
    error: new FakeElement(),
    playToggle: new FakeElement(),
    timeline: new FakeElement(),
    timeDisplay: new FakeElement(),
    muteToggle: new FakeElement(),
    volume: new FakeElement(),
    subtitle,
    audioTrack: new FakeElement(),
    speed: new FakeElement(),
    fullscreenToggle: fullscreen,
  });
  assert.doesNotThrow(() => player.fullscreen());
  player.load({ url: "/video.mp4", thumbnail: "/thumb.webp", subtitles: ["/subtitles.vtt"] }, { id: "episode" }, 12);
  assert.equal(video.poster, "/thumb.webp");
  assert.equal(video.src, "/video.mp4");
  assert.equal(subtitle.options.length, 2);
  video.duration = 100;
  video.dispatch("loadedmetadata");
  assert.equal(video.currentTime, 12);
  assert.equal(documentElement.fullscreenElement, null);
});

test("Teacher Mode enters, exits, and honors its keyboard shortcut", () => {
  const documentListeners = {};
  globalThis.document = {
    addEventListener(type, callback) { documentListeners[type] = callback; },
    createElement() { return new FakeElement(); },
  };
  globalThis.requestAnimationFrame = (callback) => callback();
  const overlay = new FakeElement();
  const exitButton = new FakeElement();
  const mode = new TeacherMode({
    overlay,
    exitButton,
    kicker: new FakeElement(),
    title: new FakeElement(),
    meta: new FakeElement(),
    body: new FakeElement(),
  });
  mode.configure({ shortcut: "KeyT", keyLabel: "T", readingPage: "/reading.html" });
  documentListeners.keydown({ code: "KeyT", target: { matches: () => false }, preventDefault() {} });
  assert.equal(mode.active, true);
  assert.equal(overlay.hidden, false);
  assert.equal(overlay.classList.values.has("is-active"), true);
  mode.deactivate();
  assert.equal(mode.active, false);
  assert.equal(overlay.hidden, true);
});
