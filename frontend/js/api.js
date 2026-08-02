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
  health: () => request("/health"),
  version: () => request("/version"),
  languages: () => request("/languages"),
  library: (query = "") => request(`/library${query ? `/search?query=${encodeURIComponent(query)}` : ""}`),
  session: () => request("/auth/session"),
  login: (credentials) => request("/auth/login", { method: "POST", body: JSON.stringify(credentials) }),
  logout: () => request("/auth/logout", { method: "POST" }),
  scan: () => request("/dashboard/library/scan", { method: "POST" }),
  episodeSource: (episodeId) => request(`/player/source/${encodeURIComponent(episodeId)}`),
  progress: (episodeId) => request(`/player/progress/${encodeURIComponent(episodeId)}`),
  saveProgress: (payload) => request("/player/progress", { method: "POST", body: JSON.stringify(payload) }),
  continueWatching: () => request("/continue"),
  favorites: () => request("/favorites"),
  addFavorite: (animeId) => request(`/favorites/${encodeURIComponent(animeId)}`, { method: "POST" }),
  removeFavorite: (animeId) => request(`/favorites/${encodeURIComponent(animeId)}`, { method: "DELETE" }),
  history: () => request("/history"),
  clearHistory: () => request("/history", { method: "DELETE" }),
};
