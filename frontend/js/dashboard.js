export class Dashboard {
  constructor(elements, callbacks = {}) {
    this.elements = elements;
    this.api = callbacks.api;
    this.getMessages = callbacks.getMessages || (() => ({}));
    this.onLibraryChanged = callbacks.onLibraryChanged || (() => {});
    this.library = { anime: [] };
    this.locale = "en";
    this.locValues = {};
    this.bind();
  }

  t(key) {
    return this.getMessages()[key] || key;
  }

  bind() {
    this.elements.scanButton.addEventListener("click", () => this.scan());
    this.elements.refreshButton.addEventListener("click", () => this.refreshDatabase());
    this.elements.userForm.addEventListener("submit", (event) => this.createUser(event));
  }

  async refresh() {
    const status = await this.api.dashboardStatus().catch(() => null);
    if (status) this.renderStats(status);
    this.library = await this.api.dashboardLibrary().catch(() => ({ anime: [] }));
    this.renderLibrary();
    await this.renderLocalization();
    await this.renderUsers();
  }

  async renderUsers() {
    const container = this.elements.usersContainer;
    container.replaceChildren();
    const users = await this.api.users().catch(() => []);
    users.forEach((user) => {
      const row = document.createElement("div");
      row.className = "user-row";
      const name = document.createElement("span");
      name.className = "user-row__name";
      name.textContent = user.username;
      const role = document.createElement("span");
      role.className = "user-row__role";
      role.textContent = user.role === "mochi" ? this.t("administrator") : this.t("member");
      const remove = document.createElement("button");
      remove.type = "button";
      remove.className = "button button--line user-row__remove";
      remove.textContent = this.t("user_delete");
      remove.addEventListener("click", async () => {
        try {
          await this.api.deleteUser(user.id);
          await this.renderUsers();
        } catch (error) { this.setStatus(error.message); }
      });
      row.append(name, role, remove);
      container.append(row);
    });
  }

  async createUser(event) {
    event.preventDefault();
    const form = new FormData(this.elements.userForm);
    try {
      await this.api.createUser(form.get("username"), form.get("password"), form.get("role"));
      this.elements.userForm.reset();
      await this.renderUsers();
    } catch (error) { this.setStatus(error.message); }
  }

  renderStats(status) {
    const stats = this.elements.stats;
    stats.hidden = false;
    stats.replaceChildren();
    const rows = [
      [this.t("dashboard_series"), status.series],
      [this.t("dashboard_tutorials"), status.tutorials],
      [this.t("dashboard_episodes"), status.episodes],
      [this.t("dashboard_users"), status.users],
      [this.t("dashboard_posters"), status.posters],
      [this.t("dashboard_banners_count"), status.banners],
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
    (this.library.anime || []).forEach((anime) => container.append(this.animeRow(anime)));
  }

  animeRow(anime) {
    const row = document.createElement("article");
    row.className = "manage-item";
    const head = document.createElement("div");
    head.className = "manage-item__head";
    const title = document.createElement("strong");
    title.textContent = anime.title;
    const meta = document.createElement("span");
    const seasonCount = (anime.seasons || []).length;
    meta.textContent = seasonCount
      ? `${seasonCount} ${seasonCount === 1 ? this.t("season") : this.t("seasons")}`
      : this.t("filter_tutorials");
    const editButton = document.createElement("button");
    editButton.type = "button";
    editButton.className = "button button--line manage-item__edit";
    editButton.textContent = this.t("dashboard_edit");
    editButton.addEventListener("click", () => { panel.hidden = !panel.hidden; editButton.textContent = panel.hidden ? this.t("dashboard_edit") : this.t("dashboard_cancel"); });
    head.append(title, meta, editButton);

    const panel = document.createElement("div");
    panel.className = "manage-item__panel";
    panel.hidden = true;
    panel.append(this.metadataForm(anime), this.episodeEditor(anime));
    row.append(head, panel);
    return row;
  }

  metadataForm(anime) {
    const form = document.createElement("div");
    form.className = "manage-form";
    form.append(this.field(this.t("dashboard_title"), "text", anime.title, "title"));
    form.append(this.field(this.t("dashboard_description"), "text", anime.description || "", "description"));
    if (anime.poster) form.append(this.field(this.t("dashboard_poster"), "text", anime.poster, "poster"));
    if (anime.banner) form.append(this.field(this.t("dashboard_banner"), "text", anime.banner, "banner"));
    const save = document.createElement("button");
    save.type = "button";
    save.className = "button button--primary";
    save.textContent = this.t("dashboard_save");
    save.addEventListener("click", async () => {
      const values = {};
      form.querySelectorAll("[data-field]").forEach((input) => { values[input.dataset.field] = input.value; });
      try {
        await this.api.editAnime(anime.id, values);
        await this.onLibraryChanged();
        await this.refresh();
      } catch (error) { this.setStatus(error.message); }
    });
    form.append(save);
    return form;
  }

  episodeEditor(anime) {
    const wrapper = document.createElement("div");
    wrapper.className = "manage-episodes";
    (anime.seasons || []).forEach((season) => {
      (season.episodes || []).forEach((episode) => {
        const line = document.createElement("div");
        line.className = "manage-episode";
        const label = document.createElement("span");
        label.textContent = `S${String(season.number).padStart(2, "0")} E${String(episode.number).padStart(2, "0")}`;
        const input = document.createElement("input");
        input.type = "text";
        input.value = episode.title || "";
        input.dataset.episode = episode.id;
        const save = document.createElement("button");
        save.type = "button";
        save.className = "manage-episode__save";
        save.textContent = this.t("dashboard_saved");
        save.disabled = true;
        input.addEventListener("input", () => { save.disabled = false; save.textContent = this.t("dashboard_save"); });
        save.addEventListener("click", async () => {
          try {
            await this.api.editEpisode(episode.id, { title: input.value });
            save.disabled = true;
            save.textContent = this.t("dashboard_saved");
          } catch (error) { this.setStatus(error.message); }
        });
        line.append(label, input, save);
        wrapper.append(line);
      });
    });
    return wrapper;
  }

  async renderLocalization() {
    const tabs = this.elements.locTabs;
    const container = this.elements.locContainer;
    tabs.replaceChildren();
    container.replaceChildren();
    ["en", "hi", "ja"].forEach((code) => {
      const tab = document.createElement("button");
      tab.type = "button";
      tab.className = "loc-tab";
      tab.textContent = code.toUpperCase();
      tab.classList.toggle("is-active", code === this.locale);
      tab.addEventListener("click", () => { this.locale = code; this.renderLocalization(); });
      tabs.append(tab);
    });
    this.locValues = await this.api.localization(this.locale).catch(() => ({}));
    const list = document.createElement("div");
    list.className = "loc-list";
    Object.entries(this.locValues).forEach(([key, value]) => {
      const row = document.createElement("label");
      row.className = "loc-row";
      const name = document.createElement("span");
      name.textContent = key;
      const input = document.createElement("textarea");
      input.rows = 2;
      input.value = String(value);
      input.dataset.locKey = key;
      row.append(name, input);
      list.append(row);
    });
    const save = document.createElement("button");
    save.type = "button";
    save.className = "button button--primary";
    save.textContent = this.t("dashboard_save");
    save.addEventListener("click", async () => {
      const values = {};
      list.querySelectorAll("[data-loc-key]").forEach((input) => { values[input.dataset.locKey] = input.value; });
      try {
        await this.api.saveLocalization(this.locale, values);
        save.textContent = this.t("dashboard_saved");
        setTimeout(() => { save.textContent = this.t("dashboard_save"); }, 1500);
      } catch (error) { this.setStatus(error.message); }
    });
    container.append(list, save);
  }

  async scan() {
    this.elements.scanStatus.textContent = this.t("dashboard_scanning");
    try {
      await this.api.scan();
      this.elements.scanStatus.textContent = this.t("dashboard_scan_complete");
      await this.onLibraryChanged();
    } catch (error) { this.elements.scanStatus.textContent = error.message; }
  }

  async refreshDatabase() {
    this.elements.scanStatus.textContent = this.t("dashboard_refreshing");
    try {
      const report = await this.api.refreshDatabase();
      this.elements.scanStatus.textContent = report.integrity === "ok"
        ? `${this.t("dashboard_db_ok")} · ${report.pruned} pruned`
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
