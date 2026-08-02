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
    this.onProgress = callbacks.onProgress || (() => {});
    this.onComplete = callbacks.onComplete || (() => {});
    this.currentEpisode = null;
    this.resumeReady = true;
    this.lastProgressAt = 0;
    this.bindEvents();
  }

  bindEvents() {
    this.playToggle.addEventListener("click", () => this.togglePlay());
    this.video.addEventListener("play", () => this.updatePlayButton());
    this.video.addEventListener("pause", () => this.updatePlayButton());
    this.video.addEventListener("timeupdate", () => this.updateProgress());
    this.video.addEventListener("loadedmetadata", () => this.updateProgress());
    this.video.addEventListener("waiting", () => this.loading.removeAttribute("hidden"));
    this.video.addEventListener("canplay", () => this.loading.setAttribute("hidden", ""));
    this.video.addEventListener("error", () => this.error.removeAttribute("hidden"));
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
    this.speed.addEventListener("change", () => { this.video.playbackRate = Number(this.speed.value); });
    this.fullscreenToggle.addEventListener("click", () => this.fullscreen());
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
    this.currentEpisode = episode;
    this.resumeReady = false;
    this.error.setAttribute("hidden", "");
    this.empty.setAttribute("hidden", "");
    this.subtitle.replaceChildren(new Option("Subtitles off", ""));
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
      if (position > 0 && position < this.video.duration) this.video.currentTime = position;
      this.resumeReady = true;
      this.updateProgress();
    }, { once: true });
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

  fullscreen() {
    const target = document.querySelector("#player-shell");
    if (!document.fullscreenElement) target.requestFullscreen?.();
    else document.exitFullscreen?.();
  }
}

function formatTime(seconds) {
  const minutes = Math.floor(seconds / 60).toString().padStart(2, "0");
  const remainder = Math.floor(seconds % 60).toString().padStart(2, "0");
  return `${minutes}:${remainder}`;
}
