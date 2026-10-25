const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");
const vm = require("node:vm");

const source = fs.readFileSync(path.join(__dirname, "..", "ui", "app.js"), "utf8");
const html = fs.readFileSync(path.join(__dirname, "..", "ui", "index.html"), "utf8");
const initialStyli = [
    { id: "30", name: "Third", hours: 900, capacity_min: 800, capacity_max: 1000, active: false },
    { id: "2", name: "Second", hours: 240, capacity_min: 500, capacity_max: 800, active: true },
    { id: "10", name: "First", hours: 100, capacity_min: 800, capacity_max: 1000, active: false },
];
const copy = value => JSON.parse(JSON.stringify(value));
const response = (data, status = 200) => ({ ok: status >= 200 && status < 300, status, json: async () => copy(data) });
const deferred = () => { let resolve, reject; const promise = new Promise((yes, no) => { resolve = yes; reject = no; }); return { promise, resolve, reject }; };

function harness() {
    const elements = new Map(), requests = [];
    let socket;
    const element = id => {
        if (!elements.has(id)) elements.set(id, {
            style: {}, disabled: false, hidden: false, textContent: "",
            classList: { add() {}, remove() {}, toggle() {} },
        });
        return elements.get(id);
    };
    const context = vm.createContext({
        document: { addEventListener() {}, getElementById: element, querySelectorAll: () => [] },
        window: {}, location: { hash: "#stylus", host: "example.test", protocol: "http:" },
        console: { error() {} }, setTimeout: () => null, clearTimeout() {}, clearInterval() {},
        WebSocket: function () { socket = this; },
        fetch: (url, options) => {
            requests.push({ url, options });
            return context.reply(url, options);
        },
    });
    vm.runInContext(source, context);
    context.reply = url => Promise.resolve(response(url === "/styli" ? initialStyli : { success: true }));
    context.renderScreensaver = () => {};
    context.remeasureActiveMarquees = () => {};
    context.setMetaText = (el, text) => { el.textContent = text; };
    context.state.mode = "stylus";
    context.connectWebSocket();
    return {
        context, requests, el: element,
        status: status => socket.onmessage({ data: JSON.stringify({ event: "status", data: { status, time: "00:00" } }) }),
        hours: (id, hours) => socket.onmessage({ data: JSON.stringify({ event: "stylus_hours", data: { stylus_id: id, hours } }) }),
        load: async () => { await context.fetchStyli(); context.render(); requests.length = 0; },
    };
}

function assertBars(h, id, width, color) {
    assert.equal(h.context.getCurrentStylus().id, id);
    assert.equal(h.context.getActiveStylus().id, id);
    assert.equal(h.el("stylus-bar-compact-fill").style.width, width);
    assert.equal(h.el("stylus-bar-full-fill").style.width, width);
    if (color) {
        assert.equal(h.el("stylus-bar-compact-fill").style.background, color);
        assert.equal(h.el("stylus-bar-full-fill").style.background, color);
    }
}

test("initial selection uses saved active flag, stable IDs, and both bars", async () => {
    const h = harness(); await h.load();
    assert.deepEqual(Array.from(h.context.state.styli, s => s.id), ["10", "2", "30"]);
    assertBars(h, "2", "30%");
    assert.equal(h.el("stylus-mode-name").textContent, "Second");
    assert.equal(h.el("stylus-mode-hours").textContent, "240.00 h");
    assert.equal(h.el("btn-next-stylus").disabled, false);
});

test("Next and Prev persist adjacent IDs with wraparound and update both capacities/colors", async () => {
    const h = harness(); await h.load();
    for (const [direction, id, width] of [
        ["nextStylus", "30", "90%"], ["nextStylus", "10", "10%"], ["nextStylus", "2", "30%"],
        ["prevStylus", "10", "10%"], ["prevStylus", "30", "90%"], ["prevStylus", "2", "30%"],
    ]) {
        await h.context[direction]();
        assert.equal(h.requests.at(-1).url, `/styli/${id}/activate`);
        assert.equal(h.requests.at(-1).options.method, "POST");
        assertBars(h, id, width);
        assert.equal(h.el("stylus-bar-compact-fill").style.background, h.el("stylus-bar-full-fill").style.background);
        assert.equal(h.context.state.styli.filter(s => s.active).length, 1);
    }
});

test("pending activation retains old selection and disables Prev/Next/Reset across mode changes", async () => {
    const h = harness(); await h.load();
    const pending = deferred();
    h.context.reply = () => pending.promise;
    const activation = h.context.nextStylus();
    assertBars(h, "2", "30%");
    for (const id of ["btn-prev-stylus", "btn-next-stylus", "btn-reset-stylus"]) assert.equal(h.el(id).disabled, true);
    h.context.prevStylus(); h.context.nextStylus(); h.context.resetStylus();
    h.context.state.mode = "sync"; h.context.renderStylusControls();
    assert.equal(h.requests.length, 1);
    pending.resolve(response({ success: true })); await activation;
    h.context.state.mode = "stylus"; h.context.render();
    assertBars(h, "30", "90%");
    for (const id of ["btn-prev-stylus", "btn-next-stylus", "btn-reset-stylus"]) assert.equal(h.el(id).disabled, false);
});

test("received playback status guards navigation across every mode and debug hash", async () => {
    for (const mode of ["standby", "play", "link", "re-link", "stylus", "sync"]) {
        for (const hash of ["", "#stylus", "#play", "#sync", "#stylus-error"]) {
            const h = harness(); await h.load();
            h.context.state.mode = mode; h.context.location.hash = hash;
            h.status("play");
            // A page/mode change cannot erase the received status.
            h.context.state.mode = "stylus"; h.context.render();
            assert.equal(h.context.state.playbackStatus, "play");
            assert.equal(h.el("btn-prev-stylus").disabled, true);
            assert.equal(h.el("btn-next-stylus").disabled, true);
            h.context.nextStylus(); h.context.prevStylus();
            assert.equal(h.requests.filter(r => r.url.endsWith("/activate")).length, 0);
            h.status("stop");
            assert.equal(h.el("btn-prev-stylus").disabled, false);
            assert.equal(h.el("btn-next-stylus").disabled, false);
        }
    }
});

test("a play status received during activation keeps navigation disabled after its success", async () => {
    const h = harness(); await h.load();
    const pending = deferred(); h.context.reply = () => pending.promise;
    const activation = h.context.nextStylus(); h.status("play");
    pending.resolve(response({ success: true })); await activation;
    assertBars(h, "30", "90%");
    assert.equal(h.el("btn-next-stylus").disabled, true);
    h.status("stop"); assert.equal(h.el("btn-next-stylus").disabled, false);
});

function assertErrorState(h) {
    assert.equal(h.context.state.stylusError, true);
    assert.equal(h.el("stylus-error").style.display, "");
    for (const id of ["stylus-mode-name", "stylus-mode-hours", "stylus-bar-full", "stylus-empty"]) {
        assert.equal(h.el(id).style.display, "none");
    }
    assert.equal(h.el("btn-reset-stylus").disabled, true);
    assert.equal(h.el("btn-reset-stylus").style.visibility, "hidden");
    assert.equal(h.el("btn-prev-stylus").disabled, false);
    assert.equal(h.el("btn-next-stylus").disabled, false);
}

test("HTTP rejection shows only the empty-style error and either navigation button retries", async () => {
    for (const status of [404, 409, 500]) {
        for (const direction of ["nextStylus", "prevStylus"]) {
            const h = harness(); await h.load();
            h.context.reply = () => Promise.resolve(response({ error: "rejected" }, status));
            await h.context[direction]();
            assert.equal(h.context.getActiveStylus().id, "2");
            assertErrorState(h);
            assert.equal(h.requests.length, 1);
            h.context.reply = () => Promise.resolve(response({ success: true }));
            await h.context[direction]();
            assert.equal(h.context.state.stylusError, false);
            assert.equal(h.el("stylus-error").style.display, "none");
            assert.equal(h.el("btn-reset-stylus").style.visibility, "");
            assertBars(h, direction === "nextStylus" ? "30" : "10", direction === "nextStylus" ? "90%" : "10%");
            assert.equal(h.requests[0].url, h.requests[1].url);
        }
    }
    assert.match(html, /id="stylus-error" class="empty-state" role="alert"[^>]*>An error occurred!</);
    assert.doesNotMatch(html, /btn-retry-stylus|stylus-selection-feedback/);
});

test("lost response refreshes the saved selection while the error waits for a navigation retry", async () => {
    for (const activationReply of [
        () => Promise.reject(new Error("connection reset after commit")),
        () => Promise.resolve({ ok: true, json: async () => { throw new Error("invalid JSON"); } }),
        () => Promise.resolve(response({ success: false })),
    ]) {
        const h = harness(); await h.load();
        const recovery = deferred();
        h.context.reply = url => url === "/styli" ? recovery.promise : activationReply();
        const activation = h.context.nextStylus();
        // Drain the rejection chain until recovery is requested.
        for (let i = 0; i < 10 && h.requests.length < 2; i++) await Promise.resolve();
        assert.equal(h.requests.at(-1).url, "/styli");
        assert.equal(h.el("btn-reset-stylus").disabled, true);
        assert.equal(h.context.state.stylusActivationPending, true);
        recovery.resolve(response(initialStyli.map(s => ({ ...s, active: s.id === "30" }))));
        await activation;
        assert.equal(h.context.getActiveStylus().id, "30");
        assert.equal(h.el("stylus-bar-compact-fill").style.width, "90%");
        assert.equal(h.context.state.stylusSelectionUnconfirmed, false);
        assertErrorState(h);
    }
});

test("after failed recovery Prev/Next reload selection before navigating in the chosen direction", async () => {
    for (const direction of ["nextStylus", "prevStylus"]) {
        const h = harness(); await h.load();
        h.context.reply = () => Promise.reject(new Error("offline"));
        await h.context.nextStylus();
        assert.equal(h.context.state.stylusActivationPending, false);
        assert.equal(h.context.state.stylusSelectionUnconfirmed, true);
        assertErrorState(h);
        h.context.resetStylus();
        const recovery = deferred();
        h.context.reply = url => url === "/styli" ? recovery.promise : Promise.resolve(response({ success: true }));
        const retry = h.context[direction]();
        assert.equal(h.context.state.stylusActivationPending, true);
        assert.equal(h.requests.at(-1).url, "/styli");
        for (const id of ["btn-prev-stylus", "btn-next-stylus", "btn-reset-stylus"]) assert.equal(h.el(id).disabled, true);
        h.context.nextStylus(); h.context.prevStylus(); h.context.resetStylus();
        assert.equal(h.requests.length, 3);
        recovery.resolve(response(initialStyli.map(s => ({ ...s, active: s.id === "30" }))));
        await retry;
        assertBars(h, direction === "nextStylus" ? "10" : "2", direction === "nextStylus" ? "10%" : "30%");
        assert.equal(h.context.state.stylusError, false);
        assert.equal(h.el("btn-next-stylus").disabled, false);
        assert.deepEqual(h.requests.map(r => r.url), ["/styli/30/activate", "/styli", "/styli", direction === "nextStylus" ? "/styli/10/activate" : "/styli/2/activate"]);
    }
});

test("failed initial loading still offers Prev/Next to reload and navigate", async () => {
    const h = harness();
    h.context.reply = () => Promise.reject(new Error("offline"));
    await h.load();
    assertErrorState(h);
    assert.equal(h.context.getActiveActionGroupId(), "actions-stylus");
    h.context.reply = url => Promise.resolve(response(url === "/styli" ? initialStyli : { success: true }));
    await h.context.prevStylus();
    assertBars(h, "10", "10%");
    assert.equal(h.context.state.stylusError, false);
});

test("another failed reload keeps the generic error and sends no activation", async () => {
    const h = harness(); await h.load();
    h.context.reply = () => Promise.reject(new Error("offline"));
    await h.context.nextStylus();
    await h.context.prevStylus();
    assertErrorState(h);
    assert.deepEqual(h.requests.map(r => r.url), ["/styli/30/activate", "/styli", "/styli"]);
});

test("playback beginning during recovery prevents the following activation", async () => {
    const h = harness(); await h.load();
    h.context.reply = () => Promise.reject(new Error("offline"));
    await h.context.nextStylus();
    const recovery = deferred(); h.context.reply = () => recovery.promise;
    const retry = h.context.prevStylus();
    h.status("play");
    recovery.resolve(response(initialStyli)); await retry;
    assert.equal(h.requests.length, 3);
    assert.equal(h.context.state.stylusError, false);
    assert.equal(h.el("btn-next-stylus").disabled, true);
    assertBars(h, "2", "30%");
});

test("stale selection fetch cannot overwrite a later confirmed activation", async () => {
    const h = harness(); await h.load();
    const stale = deferred();
    h.context.reply = url => url === "/styli" ? stale.promise : Promise.resolve(response({ success: true }));
    const oldRead = h.context.fetchStyli();
    await h.context.nextStylus();
    stale.resolve(response(initialStyli)); await oldRead; h.context.render();
    assertBars(h, "30", "90%");
});

test("live hours update both bars for active selection while other stylus hours stay separate", async () => {
    const h = harness(); await h.load();
    h.hours("2", 400); assertBars(h, "2", "50%");
    h.hours("30", 950); assertBars(h, "2", "50%");
    await h.context.nextStylus(); assertBars(h, "30", "95%");
});

test("empty and single-stylus lists send no activation and disable navigation", async () => {
    for (const data of [[], [initialStyli[1]]]) {
        const h = harness(); h.context.reply = () => Promise.resolve(response(data));
        await h.load(); h.context.nextStylus(); h.context.prevStylus();
        assert.equal(h.requests.length, 0);
        assert.equal(h.el("btn-next-stylus").disabled, true);
        assert.equal(h.el("btn-reset-stylus").disabled, data.length === 0);
    }
});
