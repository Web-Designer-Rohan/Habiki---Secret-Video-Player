export class TeacherMode {
  constructor(elements, callbacks = {}) {
    this.overlay = elements.overlay;
    this.exitButton = elements.exitButton;
    this.kicker = elements.kicker;
    this.title = elements.title;
    this.meta = elements.meta;
    this.body = elements.body;
    this.getMessages = callbacks.getMessages || (() => ({}));
    this.onActivate = callbacks.onActivate || (() => {});
    this.onDeactivate = callbacks.onDeactivate || (() => {});
    this.active = false;
    this.shortcut = "KeyT";
    this.keyLabel = "T";
    this.readingPage = "";
    this.readingText = "";
    this.bind();
  }

  configure({ shortcut = "KeyT", keyLabel = "T", readingPage = "", readingText = "" } = {}) {
    this.shortcut = shortcut;
    this.keyLabel = keyLabel;
    this.readingPage = readingPage || "";
    this.readingText = readingText || "";
  }

  bind() {
    this.exitButton.addEventListener("click", () => this.deactivate());
    this.overlay.addEventListener("click", (event) => { if (event.target === this.overlay) this.deactivate(); });
    document.addEventListener("keydown", (event) => {
      if (event.target.matches("input, select, textarea, [contenteditable]")) return;
      if (event.code === "Escape" && this.active) { this.deactivate(); return; }
      if (this.shortcut && this.shortcut !== "none" && event.code === this.shortcut) {
        event.preventDefault();
        this.toggle();
      }
    });
  }

  toggle() {
    if (this.active) this.deactivate();
    else this.activate();
  }

  activate() {
    if (this.active) return;
    this.active = true;
    this.render();
    this.overlay.hidden = false;
    this.exitButton.focus();
    requestAnimationFrame(() => this.overlay.classList.add("is-active"));
    this.onActivate();
  }

  deactivate() {
    if (!this.active) return;
    this.active = false;
    this.overlay.classList.remove("is-active");
    this.overlay.hidden = true;
    this.onDeactivate();
  }

  render() {
    const messages = this.getMessages();
    this.kicker.textContent = messages.teacher_mode || "Reading mode";
    this.exitButton.textContent = this.keyLabel
      ? `${messages.teacher_exit || "Exit reading mode"} · ${this.keyLabel}`
      : (messages.teacher_exit || "Exit reading mode");
    this.exitButton.setAttribute("aria-label", messages.teacher_exit || "Exit reading mode");
    if (this.readingPage) {
      this.body.replaceChildren();
      const frame = document.createElement("iframe");
      frame.className = "teacher__frame";
      frame.src = this.readingPage;
      frame.title = messages.teacher_mode || "Reading mode";
      this.body.append(frame);
      return;
    }
    const text = this.readingText || messages.teacher_reading_text || "";
    this.body.textContent = text;
  }

  setContent({ title = "", meta = "" } = {}) {
    if (title) this.title.textContent = title;
    if (meta) this.meta.textContent = meta;
  }
}
