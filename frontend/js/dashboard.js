export class Dashboard {
  constructor(elements, callbacks = {}) {
    this.elements = elements;
    this.api = callbacks.api;
    this.onLibraryChanged = callbacks.onLibraryChanged || (() => {});
    this.library = { entries: [] };
    this.bind();
  }

  bind() {
    this.elements.scanButton.addEventListener("click", () => this.scan());
    this.elements.refreshButton.addEventListener("click", () => this.refreshDatabase());
  }

  async refresh() {
    const status = await this.api.dashboardStatus().catch(() => null);
    if (status) this.renderStats(status);
    this.library = await this.api.dashboardLibrary().catch(() => ({ entries: [] }));
    this.renderLibrary();
  }

  renderStats(status) {
    const stats = this.elements.stats;
    stats.hidden = false;
    stats.replaceChildren();
    const rows = [
      ["Anime", status.anime],
      ["Movies", status.movies],
      ["Tutorials", status.tutorials],
      ["Other", status.other],
      ["Episodes", status.episodes],
      ["Posters", status.posters],
      ["Banners", status.banners],
    ];
    rows.forEach(([label, value]) => {
      const cell = document.createElement("div");
      cell.className = "stat-cell";
      const number = document.createElement("strong");
      number.textContent = String(value);
      const name = document.createElement("span");
      name.textContent = label;
      cell.append(number, name);
      stats.append(cell);
    });
  }

  renderLibrary() {
    const container = this.elements.libraryContainer;
    container.replaceChildren();
    (this.library.entries || []).forEach((entry) => container.append(this.entryRow(entry)));
  }

  entryRow(entry) {
    const row = document.createElement("article");
    row.className = "manage-item";
    const head = document.createElement("div");
    head.className = "manage-item__head";
    const title = document.createElement("strong");
    title.textContent = entry.title;
    const meta = document.createElement("span");
    meta.textContent = this.typeLabel(entry);
    const editButton = document.createElement("button");
    editButton.type = "button";
    editButton.className = "button button--line manage-item__edit";
    editButton.textContent = "Edit";
    const panel = document.createElement("div");
    panel.className = "manage-item__panel";
    panel.hidden = true;
    editButton.addEventListener("click", () => { panel.hidden = !panel.hidden; editButton.textContent = panel.hidden ? "Edit" : "Cancel"; });
    head.append(title, meta, editButton);
    panel.append(this.metadataForm(entry));
    row.append(head, panel);
    return row;
  }

  typeLabel(entry) {
    const seasonCount = (entry.seasons || []).length;
    if (seasonCount) return `${seasonCount} ${seasonCount === 1 ? "Season" : "Seasons"}`;
    const labels = { movie: "Movie", tutorial: "Tutorial", other: "Other" };
    return labels[entry.type] || "Standalone";
  }

  metadataForm(entry) {
    const form = document.createElement("div");
    form.className = "manage-form";
    form.append(this.field("Title", "text", entry.title, "title"));
    form.append(this.field("Description", "text", entry.description || "", "description"));
    form.append(this.field("Year", "text", entry.year || "", "year"));
    form.append(this.field("Genre", "text", (entry.genre || []).join(", "), "genre"));
    form.append(this.field("Studio", "text", entry.studio || "", "studio"));
    const hint = document.createElement("p");
    hint.className = "modal__hint";
    hint.textContent = "Edits are stored in the title's info.json next to the media; a rescan keeps them.";
    const save = document.createElement("button");
    save.type = "button";
    save.className = "button button--primary";
    save.textContent = "Save";
    save.addEventListener("click", async () => {
      const values = {};
      form.querySelectorAll("[data-field]").forEach((input) => {
        const value = input.value.trim();
        if (input.dataset.field === "year") values.year = value ? Number(value) : "";
        else if (input.dataset.field === "genre") values.genre = value ? value.split(",").map((part) => part.trim()).filter(Boolean) : "";
        else values[input.dataset.field] = value;
      });
      try {
        await this.api.editAnime(entry.id, values);
        await this.onLibraryChanged();
        await this.refresh();
      } catch (error) { this.setStatus(error.message); }
    });
    form.append(hint, save);
    return form;
  }

  async scan() {
    this.elements.scanStatus.textContent = "Scanning…";
    try {
      await this.api.scan();
      const finished = await this.waitForScan();
      if (finished) {
        const warnings = (finished.warnings || []).length;
        this.elements.scanStatus.textContent = warnings
          ? `Scan complete · ${warnings} ${warnings === 1 ? "warning" : "warnings"}`
          : "Scan complete";
        await this.onLibraryChanged();
      }
    } catch (error) { this.elements.scanStatus.textContent = error.message; }
  }

  async waitForScan(timeoutMs = 60000, intervalMs = 500) {
    const deadline = Date.now() + timeoutMs;
    while (Date.now() < deadline) {
      const status = await this.api.scanStatus().catch(() => null);
      if (status && status.status !== "scanning") return status;
      await new Promise((resolve) => setTimeout(resolve, intervalMs));
    }
    return null;
  }

  async refreshDatabase() {
    this.elements.scanStatus.textContent = "Refreshing…";
    try {
      const report = await this.api.refreshDatabase();
      this.elements.scanStatus.textContent = report.integrity === "ok"
        ? `Database OK · ${report.pruned} pruned`
        : `integrity: ${report.integrity}`;
    } catch (error) { this.elements.scanStatus.textContent = error.message; }
  }

  setStatus(message) {
    this.elements.scanStatus.textContent = message;
  }

  field(label, type, value, name) {
    const wrapper = document.createElement("label");
    wrapper.className = "manage-field";
    const span = document.createElement("span");
    span.textContent = label;
    const input = document.createElement("input");
    input.type = type;
    input.value = value || "";
    input.dataset.field = name;
    wrapper.append(span, input);
    return wrapper;
  }
}
