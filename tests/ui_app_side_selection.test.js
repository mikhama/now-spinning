const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");
const vm = require("node:vm");

const appSource = fs.readFileSync(path.join(__dirname, "..", "ui", "app.js"), "utf8");
const html = fs.readFileSync(path.join(__dirname, "..", "ui", "index.html"), "utf8");

function makeElement() {
    const classes = new Set();
    const listeners = new Map();
    return {
        classList: {
            add: function (name) { classes.add(name); },
            remove: function (name) { classes.delete(name); },
            contains: function (name) { return classes.has(name); },
        },
        style: {},
        textContent: "",
        addEventListener: function (name, handler) { listeners.set(name, handler); },
        click: function () {
            const handler = listeners.get("click");
            assert.ok(handler, "click handler is registered");
            handler();
        },
    };
}

function createHarness() {
    const elements = new Map();
    let socket;
    let onReady;

    function element(id) {
        if (!elements.has(id)) elements.set(id, makeElement());
        return elements.get(id);
    }

    const actionIds = Array.from(html.matchAll(/id="(actions-[^"]+)" class="action-group"/g), function (match) {
        return match[1];
    });
    const sectionIds = Array.from(html.matchAll(/id="(mode-[^"]+)" class="mode-section"/g), function (match) {
        return match[1];
    });

    function FakeWebSocket() {
        socket = this;
    }

    const context = vm.createContext({
        clearTimeout,
        console,
        document: {
            addEventListener: function (name, handler) {
                if (name === "DOMContentLoaded") onReady = handler;
            },
            getElementById: element,
            querySelectorAll: function (selector) {
                if (selector === ".action-group") return actionIds.map(element);
                if (selector === ".mode-section") return sectionIds.map(element);
                return [];
            },
        },
        fetch: function () { return Promise.resolve({ ok: true }); },
        location: { hash: "", host: "example.test", protocol: "http:" },
        setTimeout,
        TextDecoder,
        window: { addEventListener: function () {} },
        WebSocket: FakeWebSocket,
    });

    vm.runInContext(appSource, context, { filename: "ui/app.js" });
    context.setMetaText = function () {};
    context.render = function () {
        context.renderVisibility();
        if (context.state.mode === "standby") context.renderStandby();
        if (context.state.mode === "play") context.renderPlay();
        if (context.state.mode === "link") context.renderLink();
    };
    context.connectWebSocket();

    return {
        context,
        element,
        emit: function (message) { socket.onmessage({ data: JSON.stringify(message) }); },
        async initializeControls() {
            context.fetchRecords = function () { return Promise.resolve(); };
            context.fetchStyli = function () { return Promise.resolve(); };
            context.applyHash = function () { return false; };
            onReady();
            await new Promise(setImmediate);
        },
        activeActions: function () {
            return actionIds.filter(function (id) { return element(id).classList.contains("active"); });
        },
    };
}

function record(id, firstDuration = "05:00", secondDuration = "05:00") {
    return {
        id,
        linked: true,
        artist: "Artist",
        title: "Record " + id,
        sides: [
            { id: "A", tracks: [{ title: "A1", duration: firstDuration }, { title: "A2", duration: firstDuration }] },
            { id: "B", tracks: [{ title: "B1", duration: secondDuration }, { title: "B2", duration: secondDuration }] },
        ],
    };
}

function scan(harness, id) {
    harness.emit({ event: "scan", data: { record_id: id } });
}

function status(harness, value, time) {
    harness.emit({ event: "status", data: { status: value, time } });
}

test("NFC error and repeat scan preserve side B; a different record resets to A", function () {
    const harness = createHarness();
    const { context, element } = harness;
    context.state.records = [record("1"), record("2")];

    scan(harness, "1");
    context.switchSide();
    assert.equal(element("btn-side-standby").textContent, "Side B");

    scan(harness, null);
    assert.equal(context.state.currentRecordId, "1");
    assert.equal(context.state.currentSideIndex, 1);
    assert.equal(context.state.standbyError, "nfc");
    assert.equal(element("btn-side-standby").style.visibility, "hidden");

    scan(harness, "1");
    assert.equal(context.state.standbyError, null);
    assert.equal(context.state.currentSideIndex, 1);
    assert.equal(element("btn-side-standby").textContent, "Side B");
    assert.equal(element("btn-side-standby").style.visibility, "visible");

    harness.emit({ event: "current_record", data: { record_id: "1" } });
    assert.equal(context.state.currentSideIndex, 1);

    scan(harness, "2");
    assert.equal(context.state.currentSideIndex, 0);
    assert.equal(element("btn-side-standby").textContent, "Side A");
});

test("automatically advanced side survives NFC error, recovery, and the next Play start", function () {
    const harness = createHarness();
    const { context, element } = harness;
    context.state.records = [record("1")];

    scan(harness, "1");
    status(harness, "play", "01:00");
    status(harness, "stop");
    assert.equal(element("btn-side-standby").textContent, "Side B");

    scan(harness, null);
    scan(harness, "1");
    status(harness, "play", "00:01");
    assert.equal(context.state.currentSideIndex, 1);
    assert.equal(context.state.currentTrackIndex, 0);
    assert.equal(element("btn-side-label").textContent, "Side B");
});

test("unknown or unlinked scans clear record identity and later valid scan starts at A", function () {
    for (const invalidId of ["999", "3"]) {
        const harness = createHarness();
        const { context } = harness;
        const unlinked = record("3");
        unlinked.linked = false;
        context.state.records = [record("1"), unlinked];

        scan(harness, "1");
        context.switchSide();
        scan(harness, invalidId);
        assert.equal(context.state.currentRecordId, null);
        assert.equal(context.state.standbyError, "not-found");

        scan(harness, "1");
        assert.equal(context.state.currentSideIndex, 0);
    }
});

test("stop advances at one minute, but not after a brief earlier play", function () {
    for (const [time, expectedSide] of [["00:59", 0], ["01:00", 1]]) {
        const harness = createHarness();
        harness.context.state.records = [record("1")];
        scan(harness, "1");
        status(harness, "play", time);
        status(harness, "stop");
        assert.equal(harness.context.state.currentSideIndex, expectedSide, time);
        assert.equal(harness.context.state.currentTrackIndex, 0);
        assert.equal(harness.context.state.boardlessElapsedSeconds, null);
        assert.equal(harness.element("btn-side-standby").textContent, expectedSide ? "Side B" : "Side A");

        status(harness, "stop");
        assert.equal(harness.context.state.currentSideIndex, expectedSide, "duplicate stop must not advance twice");
    }
});

test("final 20 seconds still advances before one minute; missing duration waits", function () {
    for (const [duration, time, expectedSide] of [
        ["00:25", "00:29", 0],
        ["00:25", "00:30", 1],
        ["bad", "00:59", 0],
        ["bad", "01:00", 1],
    ]) {
        const harness = createHarness();
        harness.context.state.records = [record("1", duration, "05:00")];
        scan(harness, "1");
        status(harness, "play", time);
        status(harness, "stop");
        assert.equal(harness.context.state.currentSideIndex, expectedSide, duration + " at " + time);
    }
});

test("Play Side button changes sides and stays selected through elapsed updates and wraparound", async function () {
    const harness = createHarness();
    const { context, element } = harness;
    context.state.records = [record("1")];
    await harness.initializeControls();

    scan(harness, "1");
    status(harness, "play", "00:10");
    assert.deepEqual(harness.activeActions(), ["actions-play"]);

    element("btn-side-label").click();
    assert.equal(context.state.currentSideIndex, 1);
    assert.equal(element("btn-side-label").textContent, "Side B");
    status(harness, "play", "00:11");
    assert.equal(context.state.currentSideIndex, 1);
    assert.equal(element("btn-side-label").textContent, "Side B");

    element("btn-side-label").click();
    assert.equal(context.state.currentSideIndex, 0);
    status(harness, "play", "00:12");
    assert.equal(element("btn-side-label").textContent, "Side A");
});

test("Play Side button keeps the chosen side and final track after an overrun", async function () {
    const harness = createHarness();
    const { context, element } = harness;
    context.state.records = [record("1", "00:15", "00:10")];
    await harness.initializeControls();

    scan(harness, "1");
    status(harness, "play", "00:45");
    element("btn-side-label").click();
    assert.equal(context.state.currentSideIndex, 1);
    assert.equal(context.state.currentTrackIndex, 1);
    assert.equal(element("btn-side-label").textContent, "Side B");
    status(harness, "play", "00:46");
    assert.equal(context.state.currentSideIndex, 1);
    assert.equal(context.state.currentTrackIndex, 1);
});

test("Play Side button preserves the selected song before overrun", async function () {
    const harness = createHarness();
    const { context, element } = harness;
    context.state.records = [record("1")];
    await harness.initializeControls();

    scan(harness, "1");
    status(harness, "play", "00:10");
    context.nextSong();
    assert.equal(context.state.currentTrackIndex, 1);
    element("btn-side-label").click();
    assert.equal(context.state.currentSideIndex, 1);
    assert.equal(context.state.currentTrackIndex, 1);
    status(harness, "play", "00:11");
    assert.equal(context.state.currentTrackIndex, 1);
});

test("empty Link action bar contains only Mode and its button advances the mode", async function () {
    const harness = createHarness();
    const { context, element } = harness;
    context.state.records = [record("1")];
    await harness.initializeControls();

    context.setMode("link");
    context.render();
    assert.deepEqual(harness.activeActions(), ["actions-empty"]);
    assert.equal(element("link-empty-grid").style.display, "");
    assert.equal(element("link-grid").style.display, "none");

    const emptyMarkup = html.split('<div id="actions-empty" class="action-group">')[1].split('<!-- Play actions -->')[0];
    assert.deepEqual(Array.from(emptyMarkup.matchAll(/<button id="([^"]+)"/g), function (match) {
        return match[1];
    }), ["btn-mode-empty"]);
    element("btn-mode-empty").click();
    assert.equal(context.state.mode, "re-link");
    assert.deepEqual(harness.activeActions(), ["actions-re-link"]);

    context.state.records = [];
    context.setMode("re-link");
    context.render();
    assert.deepEqual(harness.activeActions(), ["actions-empty"]);
    context.setMode("stylus");
    context.render();
    assert.deepEqual(harness.activeActions(), ["actions-empty"]);
});
