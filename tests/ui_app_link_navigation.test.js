const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");
const vm = require("node:vm");

const appSource = fs.readFileSync(path.join(__dirname, "..", "ui", "app.js"), "utf8");

function createHarness() {
    let socket;

    function FakeWebSocket(url) {
        this.url = url;
        socket = this;
    }

    const context = vm.createContext({
        clearTimeout,
        console,
        document: {
            addEventListener: function () {},
        },
        fetch: function () {
            return Promise.reject(new Error("Unexpected fetch in navigation test"));
        },
        location: { hash: "", host: "example.test", protocol: "http:" },
        setTimeout,
        TextDecoder,
        window: {},
        WebSocket: FakeWebSocket,
    });

    vm.runInContext(appSource, context, { filename: "ui/app.js" });

    let renderCount = 0;
    context.render = function () {
        renderCount += 1;
    };
    context.connectWebSocket();

    return {
        context,
        emit: function (message) {
            socket.onmessage({ data: JSON.stringify(message) });
        },
        getRenderCount: function () { return renderCount; },
    };
}

function records(count) {
    return Array.from({ length: count }, function (_, index) {
        return { id: String(index + 1), linked: false };
    });
}

function retainSuccessfulLink(harness, index) {
    const context = harness.context;
    const record = context.state.records[index];
    context.state.mode = "link";
    context.state.linkRecordIndex = index;
    context.state.pendingLinkRecordId = record.id;
    context.state.pendingLinkMode = "link";
    harness.emit({ event: "link_success", data: { record_id: record.id } });
    return record;
}

test("normal link navigation still advances, reverses, and wraps", function () {
    const harness = createHarness();
    const context = harness.context;
    context.state.records = records(5);
    context.state.linkRecordIndex = 1;

    context.nextRecord();
    assert.equal(context.getLinkRecord().id, "3");

    context.prevRecord();
    assert.equal(context.getLinkRecord().id, "2");

    context.state.linkRecordIndex = 4;
    context.nextRecord();
    assert.equal(context.getLinkRecord().id, "1");

    context.prevRecord();
    assert.equal(context.getLinkRecord().id, "5");
});

test("next after linking record 2 selects record 3 without skipping", function () {
    const harness = createHarness();
    const context = harness.context;
    context.state.records = records(5);
    retainSuccessfulLink(harness, 1);

    assert.equal(context.getLinkRecord().id, "2");
    context.nextRecord();

    assert.equal(context.state.retainedLinkRecordId, null);
    assert.equal(context.getLinkRecord().id, "3");
    assert.equal(harness.getRenderCount(), 2);
});

test("previous after linking record 4 selects record 3", function () {
    const harness = createHarness();
    const context = harness.context;
    context.state.records = records(5);
    retainSuccessfulLink(harness, 3);

    context.prevRecord();

    assert.equal(context.state.retainedLinkRecordId, null);
    assert.equal(context.getLinkRecord().id, "3");
});

test("navigation after linking a boundary record wraps to the adjacent record", function () {
    const nextHarness = createHarness();
    nextHarness.context.state.records = records(5);
    retainSuccessfulLink(nextHarness, 4);

    nextHarness.context.nextRecord();
    assert.equal(nextHarness.context.getLinkRecord().id, "1");

    const prevHarness = createHarness();
    prevHarness.context.state.records = records(5);
    retainSuccessfulLink(prevHarness, 0);

    prevHarness.context.prevRecord();
    assert.equal(prevHarness.context.getLinkRecord().id, "5");
});

test("navigation after linking the only unlinked record renders the empty state", function () {
    ["nextRecord", "prevRecord"].forEach(function (navigationFunction) {
        const harness = createHarness();
        const context = harness.context;
        context.state.records = records(1);
        retainSuccessfulLink(harness, 0);

        context[navigationFunction]();

        assert.equal(context.state.retainedLinkRecordId, null);
        assert.equal(context.getLinkRecord(), null);
        assert.equal(context.state.linkRecordIndex, 0);
        assert.equal(harness.getRenderCount(), 2);
    });
});
