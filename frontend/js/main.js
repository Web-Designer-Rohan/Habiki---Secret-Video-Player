import { api } from "./api.js";
import { debounce, formatTime } from "./util.js";
import { Player } from "./player.js";
import { Dashboard } from "./dashboard.js";
import { TeacherMode } from "./teacher.js";
import { SettingsPanel } from "./settings.js";

const state = {
  fullLibrary: { entries: [] },
  view: { entries: [] },
  unlocked: false,
  favorites: new Set(),
  allEpisodes: [],
  welcomeSetting: "always",
  libraryQuery: { query: "", category: "all", sort: "default" },
};

const elements = {
  welcome: document.querySelector("#welcome"),
  welcomeBackdrop: document.querySelector("#welcome-backdrop"),
  application: document.querySelector("#application"),
  libraryGrid: document.querySelector("#library-grid"),
  libraryEmpty: document.querySelector("#library-empty"),
  search: document.querySelector("#library-search"),
  filters: [...document.querySelectorAll(".filter-pill")],
  sort: document.querySelector("#library-sort"),
  unlockDialog: document.querySelector("#unlock-dialog"),
  unlockForm: document.querySelector("#unlock-form"),
  unlockError: document.querySelector("#unlock-error"),
  unlockOpen: document.querySelector("#unlock-open"),
  scanStatus: document.querySelector("#scan-status"),
  continueList: document.querySelector("#continue-list"),
  continueEmpty: document.querySelector("#continue-empty"),
  favoritesList: document.querySelector("#favorites-list"),
  favoritesEmpty: document.querySelector("#favorites-empty"),
  historyList: document.querySelector("#history-list"),
  historyEmpty: document.querySelector("#history-empty"),
  historyClear: document.querySelector("#history-clear"),
  dashLocked: document.querySelector("#dash-locked"),
  dashMessage: document.querySelector("#dash-message"),
  dashUnlock: document.querySelector("#dash-unlock"),
  dashStats: document.querySelector("#dash-stats"),
  dashManage: document.querySelector("#dash-manage"),
  teacherOpen: document.querySelector("#teacher-open"),
  settingsOpen: document.querySelector("#settings-open"),
};

const player = new Player({
  video: document.querySelector("#video"),
  empty: document.querySelector("#player-empty"),
  loading: document.querySelector("#player-loading"),
  error: document.querySelector("#player-error"),
  playToggle: document.querySelector("#play-toggle"),
  timeline: document.querySelector("#timeline"),
  timeDisplay: document.querySelector("#time-display"),
  muteToggle: document.querySelector("#mute-toggle"),
  volume: document.querySelector("#volume"),
  subtitle: document.querySelector("#subtitle"),
  audioTrack: document.querySelector("#audio-track"),
  speed: document.querySelector("#speed"),
  fullscreenToggle: document.querySelector("#fullscreen-toggle"),
  prevButton: document.querySelector("#prev-episode"),
  nextButton: document.querySelector("#next-episode"),
}, {
  onProgress: savePlayback,
  onPause: savePlayback,
  onComplete: (episode) => episode && savePlayback(episode, player.video.duration, true),
  onNavigate: navigateEpisode,
});

const teacher = new TeacherMode({
  overlay: document.querySelector("#teacher"),
  exitButton: document.querySelector("#teacher-exit"),
  kicker: document.querySelector("#teacher-kicker"),
  title: document.querySelector("#teacher-title"),
  meta: document.querySelector("#teacher-meta"),
  body: document.querySelector("#teacher-body"),
}, {
  onActivate: () => {
    const episode = player.currentEpisode;
    if (!episode) return;
    teacher.setContent({
      title: episode.anime_title || "",
      meta: `Episode ${String(episode.number).padStart(2, "0")}${episode.anime_title ? ` · ${episode.anime_title}` : ""}`,
    });
  },
});

const dashboard = new Dashboard({
  scanButton: document.querySelector("#scan-library"),
  refreshButton: document.querySelector("#dash-refresh-db"),
  stats: elements.dashStats,
  libraryContainer: document.querySelector("#dash-library"),
  scanStatus: elements.scanStatus,
}, {
  api,
  onLibraryChanged: async () => {
    await refreshLibrary();
    await refreshActivity();
  },
});

const settingsPanel = new SettingsPanel({
  dialog: document.querySelector("#settings-dialog"),
  form: document.querySelector("#settings-form"),
  closeButton: document.querySelector("#settings-close"),
  error: document.querySelector("#settings-error"),
  status: document.querySelector("#settings-status"),
  fields: {
    theme: document.querySelector("#set-theme"),
    volume: document.querySelector("#set-volume"),
    speed: document.querySelector("#set-speed"),
    subtitles: document.querySelector("#set-subtitles"),
    reduceMotion: document.querySelector("#set-reduce-motion"),
    welcome: document.querySelector("#set-welcome"),
    teacherKey: document.querySelector("#set-teacher-key"),
    readingPage: document.querySelector("#set-reading-page"),
    mediaRoot: document.querySelector("#set-media-root"),
    currentPassword: document.querySelector("#set-current-password"),
    newPassword: document.querySelector("#set-new-password"),
  },
}, {
  api,
  onSaved: applySettings,
  onScan: async () => {
    const finished = await dashboard.waitForScan();
    if (!finished) {
      throw new Error("Library scan timed out");
    }
    if (finished.status === "error") {
      throw new Error(finished.error || "Library scan failed");
    }
    await refreshLibrary();
    await refreshActivity();
    elements.scanStatus.textContent = (finished.warnings || []).length
      ? `Scan complete · ${finished.warnings.length} ${finished.warnings.length === 1 ? "warning" : "warnings"}`
      : "Scan complete";
  },
});

function titleFor(entryId) {
  const entry = (state.fullLibrary?.entries || []).find((item) => item.id === entryId);
  return entry ? entry.title : entryId;
}

function enrichEpisode(episode, entry, season) {
  return { ...episode, anime_id: entry.id, anime_title: entry.title, season_number: season.number };
}

function buildEpisodeIndex() {
  state.allEpisodes = [];
  for (const entry of state.fullLibrary?.entries || []) {
    for (const season of entry.seasons || []) {
      for (const episode of season.episodes || []) {
        state.allEpisodes.push(enrichEpisode(episode, entry, season));
      }
    }
    for (const episode of entry.episodes || []) {
      state.allEpisodes.push(enrichEpisode(episode, entry, { number: 1 }));
    }
  }
  updateNavButtons();
}

function updateNavButtons() {
  const index = state.allEpisodes.findIndex((entry) => entry.id === player.currentEpisode?.id);
  player.updateNav(index > 0, index >= 0 && index < state.allEpisodes.length - 1);
}

function navigateEpisode(direction) {
  if (!state.allEpisodes.length || !player.currentEpisode) return;
  const index = state.allEpisodes.findIndex((entry) => entry.id === player.currentEpisode.id);
  const target = direction === "next" ? index + 1 : index - 1;
  if (target < 0 || target >= state.allEpisodes.length) return;
  playEpisode(state.allEpisodes[target]);
}

function entryTypeLabel(entry) {
  const seasonCount = (entry.seasons || []).length;
  if (seasonCount) return `${seasonCount} ${seasonCount === 1 ? "Season" : "Seasons"} · ${countEpisodes(entry)} ${countEpisodes(entry) === 1 ? "Episode" : "Episodes"}`;
  const labels = { movies: "Movie", tutorials: "Tutorial", other: "Other", movie: "Movie", tutorial: "Tutorial" };
  return labels[entry.type] || "Standalone";
}

function libraryCard(entry) {
  const card = document.createElement("article");
  card.className = "library-card";
  const art = document.createElement("div");
  art.className = "library-card__art";
  const letter = document.createElement("span");
  letter.className = "library-card__letter";
  letter.setAttribute("aria-hidden", "true");
  letter.textContent = entry.title.slice(0, 1).toUpperCase();
  art.append(letter);
  const poster = document.createElement("img");
  poster.className = "library-card__poster";
  poster.alt = "";
  poster.loading = "lazy";
  poster.decoding = "async";
  poster.src = api.poster(entry.id);
  poster.addEventListener("error", () => poster.remove());
  art.append(poster);
  const title = document.createElement("h4");
  title.textContent = entry.title;
  const meta = document.createElement("p");
  meta.className = "library-card__meta";
  meta.textContent = entryTypeLabel(entry);
  const browser = document.createElement("div");
  browser.className = "library-card__browser";
  const standaloneEpisodes = entry.episodes || [];
  if (!(entry.seasons || []).length && standaloneEpisodes.length) {
    const play = document.createElement("button");
    play.className = "episode-button";
    play.type = "button";
    play.textContent = "Play";
    play.addEventListener("click", () => playEpisode(enrichEpisode(standaloneEpisodes[0], entry, { number: 1 })));
    browser.append(play);
  }
  (entry.seasons || []).forEach((season) => {
    const seasonDetails = document.createElement("details");
    seasonDetails.className = "season-details";
    if (season === (entry.seasons || [])[0]) seasonDetails.open = true;
    const seasonSummary = document.createElement("summary");
    seasonSummary.textContent = `Season ${String(season.number).padStart(2, "0")} · ${season.episodes.length} ${season.episodes.length === 1 ? "Episode" : "Episodes"}`;
    const episodes = document.createElement("div");
    episodes.className = "episode-list";
    season.episodes.forEach((episode) => {
      const play = document.createElement("button");
      play.className = "episode-button";
      play.type = "button";
      play.textContent = `${String(episode.number).padStart(2, "0")} · ${episode.title}`;
      play.title = episode.title;
      play.addEventListener("click", () => playEpisode(enrichEpisode(episode, entry, season)));
      episodes.append(play);
    });
    seasonDetails.append(seasonSummary, episodes);
    browser.append(seasonDetails);
  });
  const actions = document.createElement("div");
  actions.className = "library-card__actions";
  const favorite = document.createElement("button");
  favorite.className = "library-card__favorite";
  favorite.type = "button";
  const isFavorite = state.favorites?.has(entry.id) || false;
  setFavoriteButton(favorite, entry.title, isFavorite);
  favorite.addEventListener("click", () => toggleFavorite(entry.id, entry.title, favorite));
  actions.append(favorite);
  card.append(art, title, meta, browser, actions);
  return card;
}

function countEpisodes(entry) {
  return (entry.seasons || []).reduce((total, season) => total + (season.episodes || []).length, 0)
    + (entry.episodes || []).length;
}

function renderLibrary(view = state.view) {
  state.view = view;
  const entries = view.entries || [];
  elements.libraryGrid.replaceChildren();
  elements.libraryEmpty.toggleAttribute("hidden", entries.length > 0);
  entries.forEach((entry) => elements.libraryGrid.append(libraryCard(entry)));
  updateNavButtons();
}

let libraryRequestId = 0;
let libraryAbortController = null;
async function refreshLibrary() {
  const { query, category, sort } = state.libraryQuery;
  const requestId = ++libraryRequestId;
  libraryAbortController?.abort();
  libraryAbortController = new AbortController();
  try {
    const view = await api.library(query, category, sort, libraryAbortController.signal);
    if (requestId !== libraryRequestId) return; // stale response from an older query
    renderLibrary(view);
    if (!query && category === "all" && sort === "default") {
      state.fullLibrary = view;
      buildEpisodeIndex();
    }
  } catch (error) {
    if (requestId === libraryRequestId && error.name !== "AbortError") elements.scanStatus.textContent = error.message;
  }
}

async function playEpisode(episode, position = null) {
  try {
    const [source, progress] = await Promise.all([
      api.episodeSource(episode.id),
      position === null ? api.progress(episode.id).catch(() => ({ playback_position: 0 })) : Promise.resolve({ playback_position: position }),
    ]);
    player.load(source, episode, progress.playback_position || 0);
    updateNavButtons();
    document.querySelector("#player").scrollIntoView({ behavior: "smooth", block: "start" });
  } catch (error) {
    elements.scanStatus.textContent = error.message;
  }
}

async function savePlayback(episode, position, completed = false) {
  if (!state.unlocked || !episode?.anime_id || !episode?.season_number) return;
  const payload = {
    episode_id: episode.id,
    anime_id: episode.anime_id,
    season_number: episode.season_number,
    episode_number: episode.number,
    playback_position: position,
    completed,
  };
  try {
    await api.saveProgress(payload);
  } catch (error) {
    // Retry once so a transient failure does not silently lose resume position.
    try {
      await api.saveProgress(payload);
    } catch (retryError) {
      console.warn("Playback progress could not be saved", retryError || error);
    }
  }
  if (completed) await refreshActivity();
}

function setFavoriteButton(button, title, active) {
  button.textContent = active ? "★" : "☆";
  button.setAttribute("aria-label", active ? `Remove ${title} from favorites` : `Add ${title} to favorites`);
}

async function toggleFavorite(animeId, title, button) {
  if (!state.unlocked) {
    elements.unlockDialog.showModal();
    return;
  }
  try {
    const active = state.favorites.has(animeId);
    if (active) await api.removeFavorite(animeId);
    else await api.addFavorite(animeId);
    state.favorites[active ? "delete" : "add"](animeId);
    setFavoriteButton(button, title, !active);
    await refreshActivity();
  } catch (error) { elements.scanStatus.textContent = error.message; }
}

function activityRow(label, action, removeLabel, onRemove) {
  const wrapper = document.createElement("div");
  wrapper.className = "activity-row";
  const play = document.createElement("button");
  play.className = "activity-item";
  play.type = "button";
  play.textContent = label;
  play.addEventListener("click", action);
  wrapper.append(play);
  if (onRemove) {
    const remove = document.createElement("button");
    remove.className = "activity-remove";
    remove.type = "button";
    remove.textContent = "×";
    remove.setAttribute("aria-label", removeLabel);
    remove.addEventListener("click", onRemove);
    wrapper.append(remove);
  }
  return wrapper;
}

function renderActivity(target, empty, items, labeler, action, remover = null) {
  target.replaceChildren();
  empty.toggleAttribute("hidden", items.length > 0);
  items.forEach((item) => target.append(activityRow(labeler(item), () => action(item), remover ? `Remove ${titleFor(item.anime_id)}` : "", remover ? () => remover(item) : null)));
}

async function refreshActivity() {
  if (!state.unlocked) {
    elements.continueList.replaceChildren();
    elements.favoritesList.replaceChildren();
    elements.historyList.replaceChildren();
    return;
  }
  const [continued, favorites, history] = await Promise.all([api.continueWatching(), api.favorites(), api.history()]);
  state.favorites = new Set(favorites.map((item) => item.anime_id));
  renderActivity(elements.continueList, elements.continueEmpty, continued,
    (item) => `${titleFor(item.anime_id)} · Episode ${item.episode_number} · ${formatTime(item.playback_position)}`,
    (item) => {
      const episode = findEpisode(item.episode_id);
      if (episode) playEpisode(episode, item.playback_position);
    },
    async (item) => { await api.removeContinue(item.episode_id).catch(() => {}); await refreshActivity(); });
  renderActivity(elements.favoritesList, elements.favoritesEmpty, favorites,
    (item) => `★ ${titleFor(item.anime_id)}`,
    (item) => {
      const anime = (state.fullLibrary?.entries || []).find((entry) => entry.id === item.anime_id);
      const first = anime?.seasons?.[0]?.episodes?.[0] || anime?.episodes?.[0];
      if (first) playEpisode(anime.seasons?.[0] ? enrichEpisode(first, anime, anime.seasons[0]) : enrichEpisode(first, anime, { number: 1 }));
    });
  renderActivity(elements.historyList, elements.historyEmpty, history,
    (item) => `${titleFor(item.anime_id)} · Episode ${item.episode_number}`,
    (item) => {
      const episode = findEpisode(item.episode_id);
      if (episode) playEpisode(episode);
    });
  elements.historyClear.hidden = history.length === 0;
}

function findEpisode(id) {
  for (const entry of state.fullLibrary?.entries || []) {
    for (const season of entry.seasons || []) {
      const episode = season.episodes?.find((item) => item.id === id);
      if (episode) return enrichEpisode(episode, entry, season);
    }
    const standalone = (entry.episodes || []).find((item) => item.id === id);
    if (standalone) return enrichEpisode(standalone, entry, { number: 1 });
  }
  return null;
}

function openApplication() {
  elements.welcome.classList.add("welcome--leaving");
  const animation = window.anime;
  const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches || document.documentElement.classList.contains("reduce-motion");
  if (animation && typeof animation.animate === "function" && !reducedMotion) {
    animation.animate(elements.welcome, {
      opacity: [1, 0],
      translateY: [0, -24],
      duration: 500,
      easing: "easeInOutQuad",
      complete: showApplication,
    });
  } else showApplication();
}

function showApplication() {
  elements.welcome.hidden = true;
  elements.application.hidden = false;
  window.scrollTo(0, 0);
}

function resolveWelcomeVisibility() {
  if (state.welcomeSetting === "once" && sessionStorage.getItem("hibiki.welcome-seen") === "1") {
    elements.welcome.hidden = true;
    elements.application.hidden = false;
  } else {
    sessionStorage.setItem("hibiki.welcome-seen", "1");
  }
}

async function setupWelcome() {
  try {
    const libraryView = await api.library("", "all", "default");
    const bannerEntry = (libraryView.entries || []).find((entry) => entry.banner);
    if (bannerEntry) {
      applyWelcomeBackdrop(api.banner(bannerEntry.id));
      return;
    }
  } catch { /* fall through to application banners */ }
  try {
    const { banners } = await api.banners();
    if (!banners?.length) return;
    const banner = banners[Math.floor(Math.random() * banners.length)].url;
    applyWelcomeBackdrop(banner);
  } catch { /* decorative only; keep the base gradient */ }
}

function applyWelcomeBackdrop(imageUrl) {
  const backdrop = elements.welcomeBackdrop;
  backdrop.style.backgroundImage =
    `linear-gradient(to top, var(--color-bg) 6%, color-mix(in srgb, var(--color-bg) 52%, transparent) 34%, transparent 68%), url("${imageUrl}")`;
  backdrop.style.backgroundSize = "cover, cover";
  backdrop.style.backgroundPosition = "center, center";
  requestAnimationFrame(() => backdrop.classList.add("has-banner"));
}

async function injectVersion() {
  try {
    const { version } = await api.version();
    const footerVersion = document.querySelector("#footer-version");
    if (footerVersion) footerVersion.textContent = `Hibiki / v${version} · AGPL-3.0-or-later`;
  } catch { /* keep the static fallbacks in the markup */ }
}

function teacherKeyLabel(shortcut) {
  if (!shortcut || shortcut === "none") return "";
  const labels = { KeyT: "T", F2: "F2", KeyR: "R" };
  return labels[shortcut] || shortcut;
}

function applySettings(values) {
  player.applyDefaults({
    volume: Number(values.default_volume ?? 100) / 100,
    speed: Number(values.default_speed ?? 1) || 1,
    subtitles: values.subtitles_default !== "false",
  });
  document.documentElement.classList.toggle("reduce-motion", values.reduce_motion === "true");
  teacher.configure({
    shortcut: values.teacher_shortcut || "KeyT",
    keyLabel: teacherKeyLabel(values.teacher_shortcut),
    readingPage: values.reading_page || "",
  });
  state.welcomeSetting = values.welcome_screen || "always";
}

async function applyStoredSettings() {
  if (!state.unlocked) return;
  try {
    applySettings(await api.settings());
  } catch { /* keep defaults */ }
}

function updateUnlockButton() {
  elements.unlockOpen.hidden = state.unlocked;
}

function applyDashboardState() {
  elements.dashLocked.hidden = state.unlocked;
  elements.dashStats.hidden = !state.unlocked;
  elements.dashManage.hidden = !state.unlocked;
  elements.dashMessage.textContent = "Unlock the application to manage your library and activity.";
  if (state.unlocked) dashboard.refresh().catch(() => {});
}

async function submitUnlock(event) {
  event.preventDefault();
  elements.unlockError.hidden = true;
  const form = new FormData(elements.unlockForm);
  try {
    await api.unlock(form.get("password"));
    state.unlocked = true;
    elements.unlockDialog.close();
    elements.unlockForm.reset();
    updateUnlockButton();
    await applyStoredSettings();
    renderLibrary();
    applyDashboardState();
    await refreshActivity();
  } catch (error) {
    elements.unlockError.textContent = error.message;
    elements.unlockError.hidden = false;
  }
}

// Welcome screen: buttons, swipe-up gesture, backdrop banner.
document.querySelector("#enter-library").addEventListener("click", openApplication);
document.querySelector("#swipe-entry").addEventListener("click", openApplication);
let swipeStartY = null;
elements.welcome.addEventListener("touchstart", (event) => { swipeStartY = event.touches[0].clientY; }, { passive: true });
elements.welcome.addEventListener("touchend", (event) => {
  if (swipeStartY === null) return;
  const deltaY = event.changedTouches[0].clientY - swipeStartY;
  swipeStartY = null;
  if (deltaY < -60) openApplication();
}, { passive: true });

// Unlock.
elements.unlockOpen.addEventListener("click", () => elements.unlockDialog.showModal());
document.querySelector("#unlock-close").addEventListener("click", () => elements.unlockDialog.close());
elements.unlockForm.addEventListener("submit", submitUnlock);

// Teacher Mode and Settings.
elements.teacherOpen.addEventListener("click", () => teacher.toggle());
elements.settingsOpen.addEventListener("click", () => {
  if (!state.unlocked) { elements.unlockDialog.showModal(); return; }
  settingsPanel.open();
});

// Library: search, category filters, sorting.
elements.search.addEventListener("input", debounce((event) => {
  state.libraryQuery.query = event.target.value;
  refreshLibrary();
}, 180));
elements.filters.forEach((pill) => {
  pill.addEventListener("click", () => {
    state.libraryQuery.category = pill.dataset.category;
    elements.filters.forEach((candidate) => candidate.classList.toggle("is-active", candidate === pill));
    refreshLibrary();
  });
});
elements.sort.addEventListener("change", (event) => {
  state.libraryQuery.sort = event.target.value;
  refreshLibrary();
});

// History.
elements.historyClear.addEventListener("click", async () => { await api.clearHistory().catch(() => {}); await refreshActivity(); });

// Dashboard unlock shortcut.
elements.dashUnlock.addEventListener("click", () => elements.unlockDialog.showModal());

// Boot sequence.
try {
  const status = await api.authStatus();
  state.unlocked = status.unlocked;
} catch { state.unlocked = false; }
updateUnlockButton();
await applyStoredSettings();
resolveWelcomeVisibility();
applyDashboardState();
setupWelcome();
injectVersion();
await refreshLibrary();
await refreshActivity();
