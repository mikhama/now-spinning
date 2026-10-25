const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");
const vm = require("node:vm");

const source = fs.readFileSync(path.join(__dirname, "..", "ui", "app.js"), "utf8");

function harness(boardless = false) {
    let now = 1000;
    let nextTimer = 0;
    const timers = new Map();
    const requests = [];
    const errors = [];
    const elements = new Map();
    const document = {
        addEventListener() {},
        documentElement: { getAttribute: () => boardless ? "true" : null },
        getElementById(id) {
            if (!elements.has(id)) elements.set(id, {
                id, hidden: true, disabled: false, textContent: "", attributes: {}, listeners: {},
                classList: { toggle() {} },
                addEventListener(name, callback) { (this.listeners[name] ||= []).push(callback); },
                emit(name, event = {}) {
                    event.target ||= this;
                    event.preventDefault ||= () => { event.prevented = true; };
                    for (const callback of this.listeners[name] || []) callback(event);
                    return event;
                },
                focus() { document.activeElement = this; },
                setAttribute(name, value) { this.attributes[name] = value; },
                showModal() { this.open = true; },
                close() { this.open = false; this.emit("close"); },
                getBoundingClientRect() { return { left: 100, top: 100, right: 600, bottom: 350 }; },
            });
            return elements.get(id);
        },
    };
    class ClockDate extends Date { static now() { return now; } }
    const context = vm.createContext({
        document, Date: ClockDate, console: { error: message => errors.push(message) }, window: {}, location: { hash: "" }, AbortController,
        setTimeout(callback, delay) { const id = ++nextTimer; timers.set(id, { callback, delay }); return id; },
        clearTimeout(id) { timers.delete(id); }, clearInterval() {},
        fetch(url, options) { requests.push({ url, options }); return Promise.resolve({ ok: true, json: async () => ({ success: true }) }); },
    });
    vm.runInContext(source, context);
    context.setupPowerOptions();
    return { context, document, requests, errors, timers, el: id => document.getElementById(id), tick: value => { now = value; } };
}

test("trigger uses standard click for keyboard/touch and opens with Cancel focused", () => {
    const h = harness();
    h.el("kiosk-exit-button").emit("click");
    assert.equal(h.context.powerOptionsOpen, true);
    assert.equal(h.document.activeElement.id, "power-cancel");
    assert.equal(h.el("play-screensaver").hidden, true);
    assert.equal(h.requests.length, 0);
    h.context.openPowerOptions();
    assert.equal(h.document.activeElement.id, "power-cancel");
});

test("Cancel, Escape, and backdrop dismiss without action requests and restore trigger", () => {
    for (const dismiss of [
        h => h.el("power-cancel").emit("click"),
        h => h.el("power-options-dialog").emit("cancel"),
        h => { h.el("power-options-dialog").emit("pointerdown", { clientX: 1, clientY: 1 }); h.el("power-options-dialog").emit("click", { clientX: 1, clientY: 1 }); },
    ]) {
        const h = harness();
        h.context.openPowerOptions();
        dismiss(h);
        assert.equal(h.context.powerOptionsOpen, false);
        assert.equal(h.document.activeElement.id, "kiosk-exit-button");
        assert.equal(h.requests.length, 0);
    }
});

test("inside clicks and a drag from panel to backdrop do not dismiss", () => {
    const h = harness();
    h.context.openPowerOptions();
    const dialog = h.el("power-options-dialog");
    dialog.emit("pointerdown", { clientX: 200, clientY: 200 });
    dialog.emit("click", { clientX: 200, clientY: 200 });
    assert.equal(h.context.powerOptionsOpen, true);
    dialog.emit("pointerdown", { clientX: 200, clientY: 200 });
    dialog.emit("click", { clientX: 1, clientY: 1 });
    assert.equal(h.context.powerOptionsOpen, true);
});

test("rapid reopen works before the native close event and ignores the stale event", () => {
    const h = harness();
    const dialog = h.el("power-options-dialog");
    dialog.close = function () { this.open = false; };
    h.context.openPowerOptions();
    h.context.closePowerOptions();
    assert.equal(h.context.powerOptionsOpen, false);
    assert.equal(h.document.activeElement.id, "kiosk-exit-button");
    h.context.openPowerOptions();
    dialog.emit("close");
    assert.equal(h.context.powerOptionsOpen, true);
    assert.equal(h.document.activeElement.id, "power-cancel");
});

test("Tab wraps in both directions within the open dialog", () => {
    const h = harness();
    h.context.openPowerOptions();
    const dialog = h.el("power-options-dialog");
    assert.equal(dialog.emit("keydown", { key: "Tab", shiftKey: true }).prevented, true);
    assert.equal(h.document.activeElement.id, "power-shutdown");
    dialog.emit("keydown", { key: "Tab" });
    assert.equal(h.document.activeElement.id, "power-cancel");
});

test("boardless actions close immediately without messages or destructive requests", async () => {
    const h = harness(true);
    for (const action of ["exit", "shutdown"]) {
        h.context.openPowerOptions();
        await h.context.submitPowerAction(action);
        assert.equal(h.context.powerOptionsOpen, false);
        assert.equal(h.el("power-options-dialog").open, false);
        assert.equal(h.document.activeElement.id, "kiosk-exit-button");
        assert.equal(h.context.powerActionPending, false);
    }
    assert.equal(h.errors.length, 0);
    assert.equal(h.requests.length, 0);
});

test("power debug hash only opens in boardless mode", () => {
    for (const boardless of [true, false]) {
        const h = harness(boardless);
        h.context.location.hash = "#power-options";
        h.context.setMode = () => {};
        h.context.render = () => {};
        assert.equal(h.context.applyHash(), boardless);
        assert.equal(h.context.powerOptionsOpen, boardless);
    }
});

test("actions close before the POST completes and prevent duplicate choices or reopening", async () => {
    for (const [action, endpoint] of [["exit", "/kiosk/exit"], ["shutdown", "/shutdown"]]) {
        const h = harness();
        let resolve;
        h.context.fetch = (url, options) => { h.requests.push({ url, options }); return new Promise(r => { resolve = r; }); };
        h.context.openPowerOptions();
        const pending = h.context.submitPowerAction(action);
        assert.equal(h.context.powerOptionsOpen, false);
        assert.equal(h.el("power-options-dialog").open, false);
        assert.equal(h.document.activeElement.id, "kiosk-exit-button");
        await h.context.submitPowerAction("exit");
        await h.context.submitPowerAction("shutdown");
        h.context.openPowerOptions();
        assert.equal(h.context.powerOptionsOpen, false);
        assert.equal(h.requests.length, 1);
        assert.equal(h.requests[0].url, endpoint);
        assert.equal(h.requests[0].options.method, "POST");
        resolve({ ok: true, json: async () => ({ success: true }) });
        await pending;
        assert.equal(h.context.powerOptionsOpen, false);
        assert.equal(h.errors.length, 0);
        assert.equal(h.context.powerActionPending, true);
        assert.equal(h.timers.size, 0);
    }
});

test("JSON API failures keep the modal closed and allow a deliberate retry", async () => {
    const h = harness();
    h.context.openPowerOptions();
    h.context.fetch = async () => ({ ok: false, json: async () => ({ error: "Could not save stylus usage" }) });
    await h.context.submitPowerAction("shutdown");
    assert.equal(h.errors[0], "Could not save stylus usage");
    assert.equal(h.context.powerActionPending, false);
    assert.equal(h.context.powerOptionsOpen, false);
    assert.equal(h.document.activeElement.id, "kiosk-exit-button");
    h.context.fetch = async () => ({ ok: true, json: async () => ({ success: true }) });
    h.context.openPowerOptions();
    await h.context.submitPowerAction("exit");
    assert.equal(h.context.powerOptionsOpen, false);
    assert.equal(h.context.powerActionPending, true);
});

test("connection loss and malformed acknowledgement are unconfirmed without retries", async () => {
    for (const response of [
        () => Promise.reject(new Error("connection reset")),
        async () => ({ ok: true, json: async () => { throw new Error("invalid json"); } }),
        async () => ({ ok: true, json: async () => ({}) }),
    ]) {
        const h = harness();
        let count = 0;
        h.context.fetch = () => { count++; return response(); };
        h.context.openPowerOptions();
        await h.context.submitPowerAction("exit");
        assert.match(h.errors[0], /outcome unconfirmed/);
        assert.equal(h.context.powerOptionsOpen, false);
        assert.equal(h.context.powerActionPending, false);
        assert.equal(count, 1);
        assert.equal(h.timers.size, 0);
    }
});

test("bounded client timeout reports unconfirmed and releases controls", async () => {
    const h = harness();
    h.context.fetch = (url, options) => new Promise((resolve, reject) => options.signal.addEventListener("abort", () => reject(new Error("aborted"))));
    h.context.openPowerOptions();
    const pending = h.context.submitPowerAction("shutdown");
    const timer = [...h.timers.values()][0];
    assert.equal(timer.delay, 15000);
    timer.callback();
    await pending;
    assert.match(h.errors[0], /outcome unconfirmed/);
    assert.equal(h.context.powerOptionsOpen, false);
    assert.equal(h.context.powerActionPending, false);
});

test("screensaver stays suspended across updates and gets fresh inactivity on close", () => {
    const h = harness();
    h.context.state.mode = "play";
    h.context.screensaverPlayStartedAt = 0;
    h.context.screensaverLastInteractionAt = 0;
    h.context.scheduleScreensaverActivation();
    assert.equal(h.timers.size, 1);
    h.context.openPowerOptions();
    assert.equal(h.timers.size, 0);
    h.tick(25000);
    h.context.scheduleScreensaverActivation();
    h.context.renderScreensaver();
    assert.equal(h.timers.size, 0);
    assert.equal(h.el("play-screensaver").hidden, true);
    h.context.closePowerOptions();
    assert.equal(h.context.screensaverDeadline(), 35000);
    assert.equal([...h.timers.values()][0].delay, 10000);
});
