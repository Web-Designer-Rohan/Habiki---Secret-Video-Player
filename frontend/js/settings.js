import { applyTheme, normalizeTheme } from "./themes.js";

export class SettingsPanel {
  constructor(elements, callbacks = {}) {
    this.dialog = elements.dialog;
    this.form = elements.form;
    this.closeButton = elements.closeButton;
    this.error = elements.error;
    this.status = elements.status;
    this.fields = elements.fields;
    this.api = callbacks.api;
    this.onSaved = callbacks.onSaved || (() => {});
    this.onScan = callbacks.onScan || (async () => {});
    this.onThemePreview = callbacks.onThemePreview || (() => {});
    this.current = {};
    this.bind();
  }

  bind() {
    this.closeButton.addEventListener("click", () => this.dialog.close());
    this.form.addEventListener("submit", (event) => { event.preventDefault(); this.save(); });
    this.fields.theme?.addEventListener?.("change", () => {
      const theme = applyTheme(this.fields.theme.value);
      this.onThemePreview(theme);
    });
    this.fields.volume?.addEventListener?.("input", () => this.updateVolumeValue());
  }

  open() {
    this.dialog.showModal();
    this.load();
  }

  async load() {
    this.error.hidden = true;
    this.status.hidden = true;
    const values = await this.api.settings().catch(() => ({}));
    this.current = values || {};
    this.fields.theme.value = normalizeTheme(values.theme);
    applyTheme(this.fields.theme.value);
    this.fields.volume.value = String(Number(values.default_volume ?? 100));
    this.updateVolumeValue();
    this.fields.speed.value = String(Number(values.default_speed ?? 1));
    this.fields.subtitles.checked = values.subtitles_default !== "false";
    this.fields.reduceMotion.checked = values.reduce_motion === "true";
    this.fields.welcome.value = values.welcome_screen || "always";
    this.fields.teacherKey.value = values.teacher_shortcut || "KeyT";
    this.fields.readingPage.value = values.reading_page || "";
    this.fields.currentPassword.value = "";
    this.fields.newPassword.value = "";
    const config = await this.api.getConfig().catch(() => null);
    if (config) this.fields.mediaRoot.value = config.media_root || "contents";
  }

  updateVolumeValue() {
    const output = document.querySelector("#set-volume-value");
    if (output) output.textContent = `${this.fields.volume.value}%`;
  }

  async save() {
    this.error.hidden = true;
    this.status.hidden = true;
    const newPassword = this.fields.newPassword.value;
    if (newPassword) {
      try {
        await this.api.changePassword(this.fields.currentPassword.value, newPassword);
      } catch (error) {
        this.error.textContent = error.message;
        this.error.hidden = false;
        return;
      }
    }
    const values = {
      theme: normalizeTheme(this.fields.theme.value),
      default_volume: Number(this.fields.volume.value),
      default_speed: Number(this.fields.speed.value),
      subtitles_default: this.fields.subtitles.checked ? "true" : "false",
      reduce_motion: this.fields.reduceMotion.checked ? "true" : "false",
      welcome_screen: this.fields.welcome.value,
      teacher_shortcut: this.fields.teacherKey.value,
      reading_page: this.fields.readingPage.value.trim(),
    };
    try {
      await this.api.saveSettings(values);
      const mediaRoot = this.fields.mediaRoot.value.trim() || "contents";
      const configResult = await this.api.config(mediaRoot);
      await this.onScan(configResult?.scan);
      this.current = values;
      this.fields.currentPassword.value = "";
      this.fields.newPassword.value = "";
      this.status.textContent = newPassword ? "Password changed, settings saved" : "Settings saved";
      this.status.hidden = false;
      this.onSaved(values);
    } catch (error) {
      this.error.textContent = error.message;
      this.error.hidden = false;
    }
  }
}
