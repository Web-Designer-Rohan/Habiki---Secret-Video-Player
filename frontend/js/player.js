import { formatTime } from "./util.js";

export class Player {
  constructor(elements, callbacks = {}) {
    this.video = elements.video;
    this.empty = elements.empty;
    this.loading = elements.loading;
    this.error = elements.error;
    this.playToggle = elements.playToggle;
    this.timeline = elements.timeline;
    this.timeDisplay = elements.timeDisplay;
    this.muteToggle = elements.muteToggle;
    this.volume = elements.volume;
    this.subtitle = elements.subtitle;
    this.speed = elements.speed;
    this.fullscreenToggle = elements.fullscreenToggle;
    this.audioTrack = elements.audioTrack;
    this.prevButton = elements.prevButton;
    this.nextButton = elements.nextButton;
    this.onProgress = callbacks.onProgress || (() => {});
    this.onPause = callbacks.onPause || (() => {});
    this.onComplete = callbacks.onComplete || (() => {});
    this.onNavigate = callbacks.onNavigate || (() => {});
    this.currentEpisode = null;
    this.resumeReady = true;
    this.lastProgressAt = 0;
    this.loadToken = 0;
    this.bindEvents();
  }

  bindEvents() {
    this.playToggle.addEventListener("click", () => this.togglePlay());
    this.video.addEventListener("play", () => this.updatePlayButton());
    this.video.addEventListener("pause", () => this.updatePlayButton());
    this.video.addEventListener("timeupdate", () => this.updateProgress());
    this.video.addEventListener("loadedmetadata", () => {
      this.updateProgress();
      this.refreshAudioTracks();
    });
    this.video.addEventListener("waiting", () => this.loading.removeAttribute("hidden"));
    this.video.addEventListener("canplay", () => this.loading.setAttribute("hidden", ""));
    this.video.addEventListener("error", () => this.error.removeAttribute("hidden"));
    this.video.addEventListener("pause", () => {
      if (this.resumeReady && this.currentEpisode) {
        this.onPause(this.currentEpisode, this.video.currentTime);
      }
    });
    this.video.addEventListener("ended", () => this.onComplete(this.currentEpisode));
    this.timeline.addEventListener("input", () => {
      if (this.video.duration) this.video.currentTime = (Number(this.timeline.value) / 100) * this.video.duration;
    });
    this.volume.addEventListener("input", () => {
      this.video.volume = Number(this.volume.value);
      this.video.muted = false;
      this.updateVolumeButton();
    });
    this.muteToggle.addEventListener("click", () => {
      this.video.muted = !this.video.muted;
      this.updateVolumeButton();
    });
    this.subtitle.addEventListener("change", () => {
      [...this.video.textTracks].forEach((track) => { track.mode = track.language === this.subtitle.value ? "showing" : "hidden"; });
    });
    this.audioTrack?.addEventListener("change", () => {
      const tracks = this.video.audioTracks;
      [...tracks].forEach((track) => { track.enabled = track.language === this.audioTrack.value; });
    });
    this.speed.addEventListener("change", () => { this.video.playbackRate = Number(this.speed.value); });
    this.fullscreenToggle.addEventListener("click", () => this.fullscreen());
    this.prevButton?.addEventListener("click", () => this.onNavigate("prev"));
    this.nextButton?.addEventListener("click", () => this.onNavigate("next"));
    this.video.addEventListener("dblclick", () => this.fullscreen());
    document.addEventListener("keydown", (event) => {
      if (event.target.matches("input, select, textarea")) return;
      if (event.code === "Space") { event.preventDefault(); this.togglePlay(); }
      if (event.code === "ArrowLeft") this.video.currentTime = Math.max(0, this.video.currentTime - 10);
      if (event.code === "ArrowRight") this.video.currentTime = Math.min(this.video.duration || Infinity, this.video.currentTime + 10);
      if (event.key.toLowerCase() === "m") { this.video.muted = !this.video.muted; this.updateVolumeButton(); }
      if (event.key.toLowerCase() === "f") this.fullscreen();
    });
  }

  load(source, episode, position = 0) {
    const loadToken = ++this.loadToken;
    this.currentEpisode = episode;
    this.resumeReady = false;
    this.error.setAttribute("hidden", "");
    this.empty.setAttribute("hidden", "");
    this.subtitle.replaceChildren(new Option("Subtitles off", ""));
    this.audioTrack?.replaceChildren();
    if (this.audioTrack) this.audioTrack.hidden = true;
    this.video.querySelectorAll("track").forEach((track) => track.remove());
    (source.subtitles || []).forEach((url, index) => {
      const language = ["en", "hi", "ja"][index] || `subtitle-${index + 1}`;
      const track = document.createElement("track");
      track.kind = "subtitles";
      track.label = language.toUpperCase();
      track.srclang = language;
      track.src = url;
      this.video.append(track);
      this.subtitle.append(new Option(language.toUpperCase(), language));
    });
    this.video.src = source.url;
    this.video.load();
    this.video.addEventListener("loadedmetadata", () => {
      if (loadToken !== this.loadToken) return; // a newer load replaced this one
      if (position > 0 && position < this.video.duration) this.video.currentTime = position;
      this.resumeReady = true;
      this.updateProgress();
      this.applySubtitleDefault();
    }, { once: true });
  }

  applySubtitleDefault() {
    if (this.subtitleDefault === false) return;
    const tracks = [...this.video.textTracks];
    if (!tracks.length || this.subtitle.options.length < 2) return;
    const preferred = this.subtitle.options[1].value;
    this.subtitle.value = preferred;
    tracks.forEach((track) => { track.mode = track.language === preferred ? "showing" : "hidden"; });
  }

  refreshAudioTracks() {
    const tracks = this.video.audioTracks;
    if (!tracks || tracks.length < 2) {
      this.audioTrack.hidden = true;
      return;
    }
    this.audioTrack.replaceChildren();
    [...tracks].forEach((track) => this.audioTrack.append(new Option((track.label || track.language || "Track"), track.language)));
    this.audioTrack.hidden = false;
  }

  applyDefaults({ volume = 1, speed = 1, subtitles = true } = {}) {
    if (Number.isFinite(volume)) {
      this.video.volume = Math.min(1, Math.max(0, volume));
      this.volume.value = String(this.video.volume);
      this.updateVolumeButton();
    }
    if (Number.isFinite(speed)) {
      this.video.playbackRate = speed;
      const option = [...this.speed.options].find((entry) => Number(entry.value) === speed);
      if (option) this.speed.value = option.value;
    }
    this.subtitleDefault = subtitles;
  }

  togglePlay() {
    if (this.video.paused) this.video.play().catch(() => this.error.removeAttribute("hidden"));
    else this.video.pause();
  }

  updatePlayButton() {
    this.playToggle.textContent = this.video.paused ? "▶" : "Ⅱ";
    this.playToggle.setAttribute("aria-label", this.video.paused ? "Play" : "Pause");
  }

  updateVolumeButton() {
    this.muteToggle.textContent = this.video.muted || this.video.volume === 0 ? "◌" : "◖";
  }

  updateProgress() {
    const duration = Number.isFinite(this.video.duration) ? this.video.duration : 0;
    this.timeline.value = duration ? (this.video.currentTime / duration) * 100 : 0;
    this.timeDisplay.textContent = `${formatTime(this.video.currentTime)} / ${formatTime(duration)}`;
    const now = Date.now();
    if (this.resumeReady && this.currentEpisode && now - this.lastProgressAt > 2000) {
      this.lastProgressAt = now;
      this.onProgress(this.currentEpisode, this.video.currentTime);
    }
  }

  updateNav(previousEnabled, nextEnabled) {
    if (this.prevButton) this.prevButton.disabled = !previousEnabled;
    if (this.nextButton) this.nextButton.disabled = !nextEnabled;
  }

  fullscreen() {
    const target = document.querySelector("#player-shell");
    if (!document.fullscreenElement) target.requestFullscreen?.();
    else document.exitFullscreen?.();
  }
}
