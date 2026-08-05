export class TeacherMode {
  constructor(elements, callbacks = {}) {
    this.overlay = elements.overlay;
    this.exitButton = elements.exitButton;
    this.kicker = elements.kicker;
    this.title = elements.title;
    this.meta = elements.meta;
    this.date = elements.date;
    this.body = elements.body;
    this.onActivate = callbacks.onActivate || (() => {});
    this.onDeactivate = callbacks.onDeactivate || (() => {});
    this.active = false;
    this.shortcut = "KeyT";
    this.keyLabel = "T";
    this.readingPage = "";
    this.readingText = "";
    this.opener = null;
    this.bind();
  }

  configure({ shortcut = "KeyT", keyLabel = "T", readingPage = "", readingText = "" } = {}) {
    this.shortcut = shortcut;
    this.keyLabel = keyLabel;
    this.readingPage = readingPage || "";
    this.readingText = readingText || "";
  }

  bind() {
    this.exitButton.addEventListener("click", () => this.toggle());
    document.addEventListener("keydown", (event) => {
      if (event.target.matches("input, select, textarea, [contenteditable]")) return;
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
    this.opener = typeof document !== "undefined" ? document.activeElement : null;
    this.render();
    const activation = this.onActivate();
    if (activation && typeof activation.then === "function") {
      activation.then(() => this.reveal()).catch(() => this.reveal());
    } else {
      this.reveal();
    }
  }

  reveal() {
    if (!this.active) return;
    this.overlay.hidden = false;
    this.exitButton.focus();
    requestAnimationFrame(() => this.overlay.classList.add("is-active"));
  }

  deactivate() {
    if (!this.active) return;
    this.active = false;
    this.overlay.classList.remove("is-active");
    this.overlay.hidden = true;
    this.onDeactivate();
    this.opener?.focus?.();
    this.opener = null;
  }

  render() {
    this.kicker.textContent = "Study desk";
    this.exitButton.setAttribute("aria-label", "Toggle Teacher Mode");
    this.exitButton.title = "Toggle Teacher Mode";
    if (this.date) this.date.textContent = new Intl.DateTimeFormat(undefined, { month: "short", day: "numeric", year: "numeric" }).format(new Date());
    if (this.readingPage) {
      this.body.replaceChildren();
      const frame = document.createElement("iframe");
      frame.className = "teacher__frame";
      frame.src = this.readingPage;
      frame.title = "Reading mode";
      this.body.append(frame);
      return;
    }
    const text = this.readingText || this.studyCopy();
    this.body.innerHTML = text;
  }

  studyCopy() {
    return `<article class="study-sheet"><p class="study-kicker">Foundations / 01</p><h2>Build systems that remain understandable.</h2><p class="study-lede">Software engineering is the practice of turning change into something a team can reason about. The strongest systems make their boundaries visible, keep decisions reversible, and leave the next reader a clear path.</p><div class="study-grid"><section><span class="study-number">01</span><h3>Model the problem</h3><p>Before choosing a framework, name the inputs, outputs, invariants, and failure modes. A precise model is often the fastest route to a small implementation.</p></section><section><span class="study-number">02</span><h3>Prefer clear seams</h3><p>Separate presentation, policy, and storage. When a requirement changes, one layer should absorb the change without forcing every other layer to move.</p></section><section><span class="study-number">03</span><h3>Make feedback cheap</h3><p>Tests, logs, and small commits shorten the distance between an idea and evidence. Fast feedback protects both quality and curiosity.</p></section></div><aside class="study-note"><strong>Field note</strong><p>Good engineering is not the absence of complexity. It is the deliberate placement of complexity where it can be named, tested, and maintained.</p></aside></article>`;
  }

  setContent({ title = "", meta = "" } = {}) {
    if (title) this.title.textContent = title;
    if (meta) this.meta.textContent = meta;
  }
}
