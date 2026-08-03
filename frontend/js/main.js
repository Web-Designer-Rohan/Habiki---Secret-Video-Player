import { api } from "./api.js";
import { Player } from "./player.js";
import { Dashboard } from "./dashboard.js";
import { TeacherMode } from "./teacher.js";
import { SettingsPanel } from "./settings.js";

const state = {
  language: "hi",
  messages: {},
  fullLibrary: { anime: [] },
  view: { anime: [] },
  authenticated: false,
  role: "e-mochi",
  favorites: new Set(),
  allEpisodes: [],
  welcomeSetting: "always",
  libraryQuery: { query: "", filter: "all", sort: "default" },
};

const elements = {
  welcome: document.querySelector("#welcome"),
  welcomeBackdrop: document.querySelector("#welcome-backdrop"),
  application: document.querySelector("#application"),
  libraryGrid: document.querySelector("#library-grid"),
  libraryEmpty: document.querySelector("#library-empty"),
  libraryCount: document.querySelector("#library-count"),
  search: document.querySelector("#library-search"),
  filters: [...document.querySelectorAll(".filter-pill")],
  sort: document.querySelector("#library-sort"),
  loginDialog: document.querySelector("#login-dialog"),
  aboutDialog: document.querySelector("#about-dialog"),
  loginForm: document.querySelector("#login-form"),
  loginError: document.querySelector("#login-error"),
  loginOpen: document.querySelector("#login-open"),
  logoutOpen: document.querySelector("#logout-open"),
  scanStatus: document.querySelector("#scan-status"),
  language: document.querySelector("#language-select"),
  continueList: document.querySelector("#continue-list"),
  continueEmpty: document.querySelector("#continue-empty"),
  favoritesList: document.querySelector("#favorites-list"),
  favoritesEmpty: document.querySelector("#favorites-empty"),
  historyList: document.querySelector("#history-list"),
  historyEmpty: document.querySelector("#history-empty"),
  historyClear: document.querySelector("#history-clear"),
  dashLocked: document.querySelector("#dash-locked"),
  dashMessage: document.querySelector("#dash-message"),
  dashLogin: document.querySelector("#dash-login"),
  dashStats: document.querySelector("#dash-stats"),
  dashManage: document.querySelector("#dash-manage"),
  dashLocalizationPanel: document.querySelector("#dash-localization-panel"),
  dashUsersPanel: document.querySelector("#dash-users-panel"),
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
  getMessages: () => state.messages,
  onActivate: () => {
    const episode = player.currentEpisode;
    if (!episode) return;
    teacher.setContent({
      title: episode.anime_title || "",
      meta: `${state.messages.episode_label || "Episode"} ${String(episode.number).padStart(2, "0")}${episode.anime_title ? ` · ${episode.anime_title}` : ""}`,
    });
  },
});

const dashboard = new Dashboard({
  scanButton: document.querySelector("#scan-library"),
  refreshButton: document.querySelector("#dash-refresh-db"),
  stats: elements.dashStats,
  libraryContainer: document.querySelector("#dash-library"),
  locTabs: document.querySelector("#dash-loc-tabs"),
  locContainer: document.querySelector("#dash-localization"),
  usersContainer: document.querySelector("#dash-users"),
  userForm: document.querySelector("#user-form"),
  scanStatus: elements.scanStatus,
}, {
  api,
  getMessages: () => state.messages,
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
  mediaGroup: document.querySelector("#settings-media"),
  fields: {
    language: document.querySelector("#set-language"),
    theme: document.querySelector("#set-theme"),
    volume: document.querySelector("#set-volume"),
    speed: document.querySelector("#set-speed"),
    subtitles: document.querySelector("#set-subtitles"),
    reduceMotion: document.querySelector("#set-reduce-motion"),
    welcome: document.querySelector("#set-welcome"),
    teacherKey: document.querySelector("#set-teacher-key"),
    readingPage: document.querySelector("#set-reading-page"),
    mediaFolders: document.querySelector("#set-media-folders"),
  },
}, {
  api,
  getMessages: () => state.messages,
  onSaved: applySettings,
});

async function loadMessages(language) {
  const response = await fetch(`/localization/${language}.json`);
  if (!response.ok) throw new Error("Unable to load language");
  state.messages = await response.json();
  document.documentElement.lang = language;
  document.querySelectorAll("[data-i18n]").forEach((node) => { node.textContent = state.messages[node.dataset.i18n] || node.textContent; });
  document.querySelectorAll("[data-i18n-placeholder]").forEach((node) => { node.placeholder = state.messages[node.dataset.i18nPlaceholder] || node.placeholder; });
}

function localizedCount(key, count) {
  const singular = state.messages[key] || key;
  const plural = state.messages[`${key}s`] || `${key}s`;
  return count === 1 ? singular : plural;
}

function debounce(fn, delay) {
  let timer;
  return (...args) => { clearTimeout(timer); timer = setTimeout(() => fn(...args), delay); };
}

function formatTime(seconds) {
  const minutes = Math.floor(seconds / 60).toString().padStart(2, "0");
  const remainder = Math.floor(seconds % 60).toString().padStart(2, "0");
  return `${minutes}:${remainder}`;
}

function titleFor(animeId) {
  const entry = (state.fullLibrary?.anime || []).find((item) => item.id === animeId);
  return entry ? entry.title : animeId;
}

function enrichEpisode(episode, anime, season) {
  return { ...episode, anime_id: anime.id, anime_title: anime.title, season_number: season.number };
}

function buildEpisodeIndex() {
  state.allEpisodes = [];
  for (const anime of state.fullLibrary?.anime || []) {
    for (const season of anime.seasons || []) {
      for (const episode of season.episodes || []) {
        state.allEpisodes.push(enrichEpisode(episode, anime, season));
      }
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
  const seasonCount = (entry.seasons || []).length;
  meta.textContent = seasonCount
    ? `${seasonCount} ${localizedCount("season", seasonCount)} · ${countEpisodes(entry)} ${localizedCount("episode", countEpisodes(entry))}`
    : state.messages.filter_tutorials || "Tutorial";
  const browser = document.createElement("div");
  browser.className = "library-card__browser";
  (entry.seasons || []).forEach((season) => {
    const seasonDetails = document.createElement("details");
    seasonDetails.className = "season-details";
    if (season === (entry.seasons || [])[0]) seasonDetails.open = true;
    const seasonSummary = document.createElement("summary");
    seasonSummary.textContent = `${state.messages.season || "Season"} ${String(season.number).padStart(2, "0")} · ${season.episodes.length} ${localizedCount("episode", season.episodes.length)}`;
    const episodes = document.createElement("div");
    episodes.className = "episode-list";
    season.episodes.forEach((episode) => {
      const play = document.createElement("button");
      play.className = "episode-button";
      play.type = "button";
      play.textContent = `${String(episode.number).padStart(2, "0")} · ${episode.title}`;
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
  return (entry.seasons || []).reduce((total, season) => total + (season.episodes || []).length, 0);
}

function renderLibrary(view = state.view) {
  state.view = view;
  const anime = view.anime || [];
  elements.libraryGrid.replaceChildren();
  elements.libraryEmpty.toggleAttribute("hidden", anime.length > 0);
  elements.libraryCount.textContent = `${anime.length} title${anime.length === 1 ? "" : "s"}`;
  anime.forEach((entry) => elements.libraryGrid.append(libraryCard(entry)));
  updateNavButtons();
}

let libraryRequestId = 0;
async function refreshLibrary() {
  const { query, filter, sort } = state.libraryQuery;
  const requestId = ++libraryRequestId;
  try {
    const view = await api.library(query, filter, sort);
    if (requestId !== libraryRequestId) return; // stale response from an older query
    renderLibrary(view);
    if (!query && filter === "all" && sort === "default") {
      state.fullLibrary = view;
      buildEpisodeIndex();
    }
  } catch (error) {
    if (requestId === libraryRequestId) elements.scanStatus.textContent = error.message;
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
  if (!state.authenticated || !episode?.anime_id || !episode?.season_number) return;
  await api.saveProgress({
    episode_id: episode.id,
    anime_id: episode.anime_id,
    season_number: episode.season_number,
    episode_number: episode.number,
    playback_position: position,
    completed,
  }).catch(() => {});
  if (completed) await refreshActivity();
}

function setFavoriteButton(button, title, active) {
  button.textContent = active ? "★" : "☆";
  button.setAttribute("aria-label", active ? `Remove ${title} from favorites` : `Add ${title} to favorites`);
}

async function toggleFavorite(animeId, title, button) {
  if (!state.authenticated) {
    elements.loginDialog.showModal();
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
  items.forEach((item) => target.append(activityRow(labeler(item), () => action(item), remover ? `${state.messages.continue_remove || "Remove"} ${titleFor(item.anime_id)}` : "", remover ? () => remover(item) : null)));
}

async function refreshActivity() {
  if (!state.authenticated) {
    elements.continueList.replaceChildren();
    elements.favoritesList.replaceChildren();
    elements.historyList.replaceChildren();
    return;
  }
  const [continued, favorites, history] = await Promise.all([api.continueWatching(), api.favorites(), api.history()]);
  state.favorites = new Set(favorites.map((item) => item.anime_id));
  renderActivity(elements.continueList, elements.continueEmpty, continued,
    (item) => `${titleFor(item.anime_id)} · ${state.messages.episode_label || "Episode"} ${item.episode_number} · ${formatTime(item.playback_position)}`,
    (item) => {
      const episode = findEpisode(item.episode_id);
      if (episode) playEpisode(episode, item.playback_position);
    },
    async (item) => { await api.removeContinue(item.episode_id).catch(() => {}); await refreshActivity(); });
  renderActivity(elements.favoritesList, elements.favoritesEmpty, favorites,
    (item) => `★ ${titleFor(item.anime_id)}`,
    (item) => {
      const anime = (state.fullLibrary?.anime || []).find((entry) => entry.id === item.anime_id);
      if (anime?.seasons?.[0]?.episodes?.[0]) playEpisode(enrichEpisode(anime.seasons[0].episodes[0], anime, anime.seasons[0]));
    });
  renderActivity(elements.historyList, elements.historyEmpty, history,
    (item) => `${titleFor(item.anime_id)} · ${state.messages.episode_label || "Episode"} ${item.episode_number}`,
    (item) => {
      const episode = findEpisode(item.episode_id);
      if (episode) playEpisode(episode);
    });
  elements.historyClear.hidden = history.length === 0;
}

function findEpisode(id) {
  for (const anime of state.fullLibrary?.anime || []) {
    for (const season of anime.seasons || []) {
      const episode = season.episodes?.find((entry) => entry.id === id);
      if (episode) return enrichEpisode(episode, anime, season);
    }
  }
  return null;
}

function openApplication() {
  elements.welcome.classList.add("welcome--leaving");
  const animation = window.anime;
  const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches || document.documentElement.classList.contains("reduce-motion");
  if (animation && !reducedMotion) animation({ targets: elements.welcome, opacity: [1, 0], translateY: [0, -24], duration: 500, easing: "easeInOutQuad", complete: showApplication });
  else showApplication();
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
    const { banners } = await api.banners();
    if (!banners?.length) return;
    const banner = banners[Math.floor(Math.random() * banners.length)].url;
    const backdrop = elements.welcomeBackdrop;
    backdrop.style.backgroundImage =
      `linear-gradient(to top, var(--color-bg) 6%, color-mix(in srgb, var(--color-bg) 52%, transparent) 34%, transparent 68%), url("${banner}")`;
    backdrop.style.backgroundSize = "cover, cover";
    backdrop.style.backgroundPosition = "center, center";
    requestAnimationFrame(() => backdrop.classList.add("has-banner"));
  } catch { /* decorative only; keep the base gradient */ }
}

function teacherKeyLabel(shortcut) {
  if (!shortcut || shortcut === "none") return "";
  const labels = { KeyT: "T", F2: "F2", KeyR: "R" };
  return labels[shortcut] || shortcut;
}

function applySettings(values) {
  player.applyDefaults({
    volume: (Number(values.default_volume ?? 100) || 100) / 100,
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
  const language = values.language;
  if (language && ["hi", "en", "ja"].includes(language) && language !== state.language) {
    state.language = language;
    elements.language.value = language;
    loadMessages(language).then(() => renderLibrary());
  }
}

async function applyStoredSettings() {
  if (!state.authenticated) return;
  try {
    applySettings(await api.settings());
  } catch { /* keep defaults */ }
}

function updateAuthButtons() {
  elements.loginOpen.hidden = state.authenticated;
  elements.logoutOpen.hidden = !state.authenticated;
}

function applyDashboardState() {
  const isAdmin = state.authenticated && state.role === "mochi";
  elements.dashLocked.hidden = isAdmin;
  elements.dashStats.hidden = !isAdmin;
  elements.dashManage.hidden = !isAdmin;
  elements.dashLocalizationPanel.hidden = !isAdmin;
  elements.dashUsersPanel.hidden = !isAdmin;
  elements.dashLogin.hidden = state.authenticated;
  elements.dashMessage.textContent = state.authenticated
    ? state.messages.dashboard_member || "Member accounts can browse and watch. Administration requires a Mochi account."
    : state.messages.dashboard_need_login || "Sign in as administrator to manage the library.";
  if (isAdmin) dashboard.refresh().catch(() => {});
}

async function logout() {
  try { await api.logout(); } catch { /* session may already be gone */ }
  state.authenticated = false;
  state.role = "e-mochi";
  updateAuthButtons();
  applyDashboardState();
  renderLibrary();
  await refreshActivity();
}

async function submitLogin(event) {
  event.preventDefault();
  elements.loginError.hidden = true;
  const form = new FormData(elements.loginForm);
  try {
    await api.login({ username: form.get("username"), password: form.get("password") });
    const session = await api.session();
    state.authenticated = true;
    state.role = session.role;
    elements.loginDialog.close();
    updateAuthButtons();
    await applyStoredSettings();
    renderLibrary();
    applyDashboardState();
    await refreshActivity();
  } catch (error) {
    elements.loginError.textContent = error.message;
    elements.loginError.hidden = false;
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

// Authentication.
elements.loginOpen.addEventListener("click", () => elements.loginDialog.showModal());
elements.logoutOpen.addEventListener("click", logout);
document.querySelector("#login-close").addEventListener("click", () => elements.loginDialog.close());
elements.loginForm.addEventListener("submit", submitLogin);

// About.
document.querySelector("#about-open").addEventListener("click", () => elements.aboutDialog.showModal());
document.querySelector("#about-footer").addEventListener("click", () => elements.aboutDialog.showModal());
document.querySelector("#about-close").addEventListener("click", () => elements.aboutDialog.close());

// Teacher Mode and Settings.
elements.teacherOpen.addEventListener("click", () => teacher.toggle());
elements.settingsOpen.addEventListener("click", () => {
  if (!state.authenticated) { elements.loginDialog.showModal(); return; }
  settingsPanel.isAdmin = state.authenticated && state.role === "mochi";
  settingsPanel.open();
});

// Library: search, filters, sorting.
elements.search.addEventListener("input", debounce((event) => {
  state.libraryQuery.query = event.target.value;
  refreshLibrary();
}, 180));
elements.filters.forEach((pill) => {
  pill.addEventListener("click", () => {
    state.libraryQuery.filter = pill.dataset.filter;
    elements.filters.forEach((candidate) => candidate.classList.toggle("is-active", candidate === pill));
    refreshLibrary();
  });
});
elements.sort.addEventListener("change", (event) => {
  state.libraryQuery.sort = event.target.value;
  refreshLibrary();
});

// Language switch.
elements.language.addEventListener("change", async (event) => {
  state.language = event.target.value;
  await loadMessages(state.language);
  renderLibrary();
  applyDashboardState();
  if (state.authenticated) api.language(state.language).catch(() => {});
});

// History.
elements.historyClear.addEventListener("click", async () => { await api.clearHistory().catch(() => {}); await refreshActivity(); });

// Dashboard sign-in shortcut.
elements.dashLogin.addEventListener("click", () => elements.loginDialog.showModal());

// Boot sequence.
await loadMessages(state.language);
try {
  const session = await api.session();
  state.authenticated = true;
  state.role = session.role;
} catch { state.authenticated = false; }
updateAuthButtons();
await applyStoredSettings();
resolveWelcomeVisibility();
applyDashboardState();
setupWelcome();
await refreshLibrary();
await refreshActivity();
