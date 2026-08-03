import { api } from "./api.js";
import { Player } from "./player.js";

const state = { language: "hi", messages: {}, library: { anime: [] }, authenticated: false, favorites: new Set() };
const elements = {
  welcome: document.querySelector("#welcome"),
  application: document.querySelector("#application"),
  libraryGrid: document.querySelector("#library-grid"),
  libraryEmpty: document.querySelector("#library-empty"),
  libraryCount: document.querySelector("#library-count"),
  search: document.querySelector("#library-search"),
  loginDialog: document.querySelector("#login-dialog"),
  aboutDialog: document.querySelector("#about-dialog"),
  loginForm: document.querySelector("#login-form"),
  loginError: document.querySelector("#login-error"),
  scanStatus: document.querySelector("#scan-status"),
  language: document.querySelector("#language-select"),
  continueList: document.querySelector("#continue-list"),
  continueEmpty: document.querySelector("#continue-empty"),
  favoritesList: document.querySelector("#favorites-list"),
  favoritesEmpty: document.querySelector("#favorites-empty"),
  historyList: document.querySelector("#history-list"),
  historyEmpty: document.querySelector("#history-empty"),
  historyClear: document.querySelector("#history-clear"),
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
  speed: document.querySelector("#speed"),
  fullscreenToggle: document.querySelector("#fullscreen-toggle"),
}, {
  onProgress: savePlayback,
  onComplete: (episode) => episode && savePlayback(episode, player.video.duration, true),
});

async function loadMessages(language) {
  const response = await fetch(`/localization/${language}.json`);
  if (!response.ok) throw new Error("Unable to load language");
  state.messages = await response.json();
  document.documentElement.lang = language;
  document.querySelectorAll("[data-i18n]").forEach((node) => { node.textContent = state.messages[node.dataset.i18n] || node.textContent; });
  document.querySelectorAll("[data-i18n-placeholder]").forEach((node) => { node.placeholder = state.messages[node.dataset.i18nPlaceholder] || node.placeholder; });
}

function renderLibrary(library = state.library) {
  state.library = library;
  const anime = library.anime || [];
  elements.libraryGrid.replaceChildren();
  elements.libraryEmpty.toggleAttribute("hidden", anime.length > 0);
  elements.libraryCount.textContent = `${anime.length} title${anime.length === 1 ? "" : "s"}`;
  anime.forEach((entry) => {
    const card = document.createElement("article");
    card.className = "library-card";
    const art = document.createElement("div");
    art.className = "library-card__art";
    art.setAttribute("aria-hidden", "true");
    art.textContent = entry.title.slice(0, 1).toUpperCase();
    const title = document.createElement("h4");
    title.textContent = entry.title;
    const meta = document.createElement("p");
    meta.className = "library-card__meta";
    meta.textContent = `${entry.seasons.length} ${localizedCount("season", entry.seasons.length)}`;
    const browser = document.createElement("div");
    browser.className = "library-card__browser";
    entry.seasons.forEach((season) => {
      const seasonDetails = document.createElement("details");
      seasonDetails.className = "season-details";
      if (season === entry.seasons[0]) seasonDetails.open = true;
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
    elements.libraryGrid.append(card);
  });
}

function localizedCount(key, count) {
  const singular = state.messages[key] || key;
  const plural = state.messages[`${key}s`] || `${key}s`;
  return count === 1 ? singular : plural;
}

function enrichEpisode(episode, anime, season) {
  return { ...episode, anime_id: anime.id, season_number: season.number };
}

async function playEpisode(episode, position = null) {
  try {
    const [source, progress] = await Promise.all([api.episodeSource(episode.id), position === null ? api.progress(episode.id).catch(() => ({ playback_position: 0 })) : Promise.resolve({ playback_position: position })]);
    player.load(source, episode, progress.playback_position || 0);
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

function activityItem(label, action) {
  const item = document.createElement("button");
  item.className = "activity-item";
  item.type = "button";
  item.textContent = label;
  item.addEventListener("click", action);
  return item;
}

function renderActivity(target, empty, items, labeler, action) {
  target.replaceChildren();
  empty.toggleAttribute("hidden", items.length > 0);
  items.forEach((item) => target.append(activityItem(labeler(item), () => action(item))));
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
  renderActivity(elements.continueList, elements.continueEmpty, continued, (item) => `${item.anime_id} · Episode ${item.episode_number} · ${Math.round(item.playback_position)}s`, (item) => {
    const episode = findEpisode(item.episode_id);
    if (episode) playEpisode(episode, item.playback_position);
  });
  renderActivity(elements.favoritesList, elements.favoritesEmpty, favorites, (item) => `★ ${item.anime_id}`, (item) => {
    const anime = state.library.anime.find((entry) => entry.id === item.anime_id);
    if (anime?.seasons?.[0]?.episodes?.[0]) playEpisode(enrichEpisode(anime.seasons[0].episodes[0], anime, anime.seasons[0]));
  });
  renderActivity(elements.historyList, elements.historyEmpty, history, (item) => `${item.anime_id} · Episode ${item.episode_number}`, (item) => {
    const episode = findEpisode(item.episode_id);
    if (episode) playEpisode(episode);
  });
  elements.historyClear.hidden = history.length === 0;
}

function findEpisode(id) {
  for (const anime of state.library.anime || []) {
    for (const season of anime.seasons || []) {
      const episode = season.episodes?.find((entry) => entry.id === id);
      if (episode) return { ...episode, anime_id: anime.id, season_number: season.number };
    }
  }
  return null;
}

async function refreshLibrary(query = "") {
  try {
    renderLibrary(await api.library(query));
    await refreshActivity();
  } catch (error) { elements.scanStatus.textContent = error.message; }
}

function openApplication() {
  elements.welcome.classList.add("welcome--leaving");
  const animation = window.anime;
  const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  if (animation && !reducedMotion) animation({ targets: elements.welcome, opacity: [1, 0], translateY: [0, -24], duration: 500, easing: "easeInOutQuad", complete: showApplication });
  else showApplication();
}

function showApplication() {
  elements.welcome.hidden = true;
  elements.application.hidden = false;
  window.scrollTo(0, 0);
}

async function applyStoredSettings() {
  if (!state.authenticated) return;
  try {
    const settings = await api.settings();
    const saved = settings?.language;
    if (saved && ["hi", "en", "ja"].includes(saved) && saved !== state.language) {
      state.language = saved;
      elements.language.value = saved;
      await loadMessages(saved);
    }
  } catch { /* keep the current language */ }
}

async function submitLogin(event) {
  event.preventDefault();
  elements.loginError.hidden = true;
  const form = new FormData(elements.loginForm);
  try {
    await api.login({ username: form.get("username"), password: form.get("password") });
    state.authenticated = true;
    elements.loginDialog.close();
    await applyStoredSettings();
    renderLibrary();
    await refreshActivity();
  } catch (error) { elements.loginError.textContent = error.message; elements.loginError.hidden = false; }
}

async function scanLibrary() {
  if (!state.authenticated) { elements.loginDialog.showModal(); return; }
  elements.scanStatus.textContent = "Scanning…";
  try {
    await api.scan();
    await refreshLibrary();
    elements.scanStatus.textContent = "Scan complete";
  } catch (error) { elements.scanStatus.textContent = error.message; }
}

document.querySelector("#enter-library").addEventListener("click", openApplication);
document.querySelector("#swipe-entry").addEventListener("click", openApplication);
document.querySelector("#login-open").addEventListener("click", () => elements.loginDialog.showModal());
document.querySelector("#login-close").addEventListener("click", () => elements.loginDialog.close());
document.querySelector("#about-open").addEventListener("click", () => elements.aboutDialog.showModal());
document.querySelector("#about-footer").addEventListener("click", () => elements.aboutDialog.showModal());
document.querySelector("#about-close").addEventListener("click", () => elements.aboutDialog.close());
elements.loginForm.addEventListener("submit", submitLogin);
document.querySelector("#scan-library").addEventListener("click", scanLibrary);
elements.search.addEventListener("input", (event) => refreshLibrary(event.target.value));
elements.language.addEventListener("change", async (event) => {
  state.language = event.target.value;
  await loadMessages(state.language);
  renderLibrary();
  if (state.authenticated) api.language(state.language).catch(() => {});
});
elements.historyClear.addEventListener("click", async () => { await api.clearHistory(); await refreshActivity(); });

await loadMessages(state.language);
try { state.authenticated = Boolean(await api.session()); } catch { state.authenticated = false; }
await applyStoredSettings();
await refreshLibrary();
