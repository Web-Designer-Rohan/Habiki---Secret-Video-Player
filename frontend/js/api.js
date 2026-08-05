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
  library: (query = "", category = "all", sort = "default", signal) =>
    request(`/library/search?query=${encodeURIComponent(query)}&category=${encodeURIComponent(category)}&sort=${encodeURIComponent(sort)}`, { signal }),
  poster: (entryId) => `/api/v1/library/${encodeURIComponent(entryId)}/poster`,
  banner: (entryId) => `/api/v1/library/${encodeURIComponent(entryId)}/banner`,
  thumbnail: (episodeId) => `/api/v1/player/thumbnail/${encodeURIComponent(episodeId)}`,
  banners: () => request("/banners"),
  version: () => request("/version"),
  authStatus: () => request("/auth/status"),
  unlock: (password) => request("/auth/unlock", { method: "POST", body: JSON.stringify({ password }) }),
  changePassword: (currentPassword, newPassword) => request("/auth/password", { method: "PUT", body: JSON.stringify({ current_password: currentPassword, new_password: newPassword }) }),
  scan: () => request("/dashboard/library/scan", { method: "POST" }),
  scanStatus: () => request("/dashboard/scan/status"),
  dashboardStatus: () => request("/dashboard/status"),
  dashboardLibrary: () => request("/dashboard/library"),
  editAnime: (animeId, values) => request(`/dashboard/anime/${encodeURIComponent(animeId)}`, { method: "PATCH", body: JSON.stringify(values) }),
  refreshDatabase: () => request("/dashboard/database/refresh", { method: "POST" }),
  config: (mediaRoot) => request("/dashboard/config", { method: "POST", body: JSON.stringify({ media_root: mediaRoot }) }),
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
};
