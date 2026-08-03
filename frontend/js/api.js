const API_ROOT = "/api/v1";

export async function request(path, options = {}) {
  const response = await fetch(`${API_ROOT}${path}`, {
    credentials: "same-origin",
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  const body = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(body?.error?.message || body?.detail || "Request failed");
  }
  return body.data;
}

export const api = {
  library: (query = "", filter = "all", sort = "default") =>
    request(`/library/search?query=${encodeURIComponent(query)}&filter=${encodeURIComponent(filter)}&sort=${encodeURIComponent(sort)}`),
  poster: (animeId) => `/api/v1/library/${encodeURIComponent(animeId)}/poster`,
  banners: () => request("/banners"),
  session: () => request("/auth/session"),
  login: (credentials) => request("/auth/login", { method: "POST", body: JSON.stringify(credentials) }),
  logout: () => request("/auth/logout", { method: "POST" }),
  scan: () => request("/dashboard/library/scan", { method: "POST" }),
  users: () => request("/users"),
  createUser: (username, password, role) => request("/users", { method: "POST", body: JSON.stringify({ username, password, role }) }),
  deleteUser: (userId) => request(`/users/${encodeURIComponent(userId)}`, { method: "DELETE" }),
  dashboardStatus: () => request("/dashboard/status"),
  dashboardLibrary: () => request("/dashboard/library"),
  editAnime: (animeId, values) => request(`/dashboard/anime/${encodeURIComponent(animeId)}`, { method: "PATCH", body: JSON.stringify(values) }),
  editEpisode: (episodeId, values) => request(`/dashboard/episode/${encodeURIComponent(episodeId)}`, { method: "PATCH", body: JSON.stringify(values) }),
  localization: (code) => request(`/dashboard/localization/${code}`),
  saveLocalization: (code, values) => request(`/dashboard/localization/${code}`, { method: "PUT", body: JSON.stringify({ values }) }),
  refreshDatabase: () => request("/dashboard/database/refresh", { method: "POST" }),
  config: (libraryPaths, language) => request("/dashboard/config", { method: "POST", body: JSON.stringify({ library_paths: libraryPaths, language }) }),
  getConfig: () => request("/dashboard/config"),
  episodeSource: (episodeId) => request(`/player/source/${encodeURIComponent(episodeId)}`),
  progress: (episodeId) => request(`/player/progress/${encodeURIComponent(episodeId)}`),
  saveProgress: (payload) => request("/player/progress", { method: "POST", body: JSON.stringify(payload) }),
  continueWatching: () => request("/continue"),
  removeContinue: (episodeId) => request(`/continue/${encodeURIComponent(episodeId)}`, { method: "DELETE" }),
  favorites: () => request("/favorites"),
  addFavorite: (animeId) => request(`/favorites/${encodeURIComponent(animeId)}`, { method: "POST" }),
  removeFavorite: (animeId) => request(`/favorites/${encodeURIComponent(animeId)}`, { method: "DELETE" }),
  history: () => request("/history"),
  clearHistory: () => request("/history", { method: "DELETE" }),
  settings: () => request("/settings"),
  saveSettings: (values) => request("/settings", { method: "PUT", body: JSON.stringify({ values }) }),
  language: (code) => request("/language", { method: "POST", body: JSON.stringify({ values: { language: code } }) }),
};
