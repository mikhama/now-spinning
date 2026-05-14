// ---------------------------------------------------------------------------
// State
// ---------------------------------------------------------------------------

var state = {
    mode: "standby",
    records: [],
    styli: [],
    currentRecordId: null,
    currentTrackIndex: 0,
    currentSideIndex: 0,
    linkRecordIndex: 0,
    reLinkRecordIndex: 0,
    stylusIndex: 0,
    stylusHours: {},
    temperature: null,
    linkError: false,
    standbyError: null, // null | "nfc" | "not-found"
};

// ---------------------------------------------------------------------------
// Mode switching
// ---------------------------------------------------------------------------

var MODES = ["standby", "play", "link", "re-link", "stylus"];

function nextMode() {
    var i = MODES.indexOf(state.mode);
    state.mode = MODES[(i + 1) % MODES.length];
    state.linkError = false;
    render();
}

// ---------------------------------------------------------------------------
// Data helpers
// ---------------------------------------------------------------------------

function getCurrentRecord() {
    if (!state.currentRecordId || state.records.length === 0) return null;
    return state.records.find(function (r) { return r.id === state.currentRecordId; }) || null;
}

function getLinkRecord() {
    if (state.records.length === 0) return null;
    return state.records[state.linkRecordIndex] || null;
}

function getLinkedRecords() {
    return state.records.filter(function (r) { return r.linked; });
}

function getReLinkRecord() {
    var linked = getLinkedRecords();
    if (linked.length === 0) return null;
    return linked[state.reLinkRecordIndex] || null;
}

function getCurrentStylus() {
    if (state.styli.length === 0) return null;
    return state.styli[state.stylusIndex] || null;
}

function coverImageUrl(record) {
    if (!record || !record.cover_image) return "";
    return "/" + record.cover_image.replace(/^ui\//, "");
}

function getStylusHours(stylus) {
    if (!stylus) return 0;
    return state.stylusHours[stylus.id] !== undefined ? state.stylusHours[stylus.id] : stylus.hours;
}

function getBarFillRatio(hours, capacityMax) {
    return Math.min(hours / capacityMax, 1);
}

function getBarColor(hours, capacityMin) {
    return hours < capacityMin ? "--ink-soft" : "--amber-deep";
}

// ---------------------------------------------------------------------------
// Render
// ---------------------------------------------------------------------------

function getModeLabel() {
    if (state.mode === "link") {
        var record = getLinkRecord();
        if (record && record.linked) return "Re-Link";
        return "Link";
    }
    if (state.mode === "re-link") return "Re-Link";
    return { standby: "Standby", play: "Play", stylus: "Stylus" }[state.mode] || state.mode;
}

function render() {
    // Top bar — mode label
    document.getElementById("mode-label").textContent = getModeLabel();

    // Top bar — stylus compact bar + temperature
    var topStylus = state.styli.length > 0 ? state.styli[0] : null;
    var compactBar = document.getElementById("stylus-bar-compact");
    var compactFill = document.getElementById("stylus-bar-compact-fill");
    var tempDisplay = document.getElementById("temperature-display");

    if (topStylus) {
        var topHours = getStylusHours(topStylus);
        var topRatio = getBarFillRatio(topHours, topStylus.capacity_max);
        var topColor = getBarColor(topHours, topStylus.capacity_min);
        compactBar.style.display = "";
        compactFill.style.width = (topRatio * 100) + "%";
        compactFill.style.background = "var(" + topColor + ")";
    } else {
        compactBar.style.display = "none";
    }

    tempDisplay.textContent = state.temperature !== null ? Math.round(state.temperature) + " °C" : "N/A";

    // Hide all mode sections and action groups
    var sections = document.querySelectorAll(".mode-section");
    for (var i = 0; i < sections.length; i++) sections[i].classList.remove("active");
    var groups = document.querySelectorAll(".action-group");
    for (var j = 0; j < groups.length; j++) groups[j].classList.remove("active");

    // Show current mode
    document.getElementById("mode-" + state.mode).classList.add("active");

    switch (state.mode) {
        case "standby":
            renderStandby();
            document.getElementById("actions-standby").classList.add("active");
            break;
        case "play":
            renderPlay();
            document.getElementById("actions-play").classList.add("active");
            break;
        case "link":
            renderLink();
            document.getElementById(state.records.length > 0 ? "actions-link" : "actions-standby").classList.add("active");
            break;
        case "re-link":
            renderReLink();
            document.getElementById(getLinkedRecords().length > 0 ? "actions-re-link" : "actions-standby").classList.add("active");
            break;
        case "stylus":
            renderStylus();
            document.getElementById(state.styli.length > 0 ? "actions-stylus" : "actions-standby").classList.add("active");
            if (state.styli.length === 0) {
                document.getElementById("btn-side-standby").style.visibility = "hidden";
            }
            break;
    }
}

function renderStandby() {
    var record = getCurrentRecord();
    var grid = document.getElementById("standby-grid");
    var errorGrid = document.getElementById("standby-error-grid");
    var notFoundGrid = document.getElementById("standby-not-found-grid");
    var sideBtn = document.getElementById("btn-side-standby");

    grid.style.display = "none";
    errorGrid.style.display = "none";
    notFoundGrid.style.display = "none";
    sideBtn.style.visibility = "hidden";

    if (state.standbyError === "nfc") {
        errorGrid.style.display = "";
    } else if (state.standbyError === "not-found") {
        notFoundGrid.style.display = "";
    } else if (record) {
        grid.style.display = "";
        sideBtn.style.visibility = "visible";
        document.getElementById("standby-cover").src = coverImageUrl(record);
        document.getElementById("standby-id").textContent = String(record.id).padStart(2, "0");
        document.getElementById("standby-artist").textContent = record.artist;
        document.getElementById("standby-title").textContent = record.title;
        if (record.sides && record.sides.length > 0) {
            var side = record.sides[state.currentSideIndex] || record.sides[0];
            sideBtn.textContent = "Side " + side.id;
        }
    } else {
        notFoundGrid.style.display = "";
    }
}

function renderPlay() {
    var record = getCurrentRecord();
    var cover = document.getElementById("play-cover");
    var trackEl = document.getElementById("play-track");
    var sideLabel = document.getElementById("btn-side-label");

    if (record && record.sides && record.sides.length > 0) {
        var side = record.sides[state.currentSideIndex] || record.sides[0];
        var track = side.tracks[state.currentTrackIndex] || side.tracks[0];

        cover.src = coverImageUrl(record);
        document.getElementById("play-id").textContent = String(record.id).padStart(2, "0");
        document.getElementById("play-artist").textContent = record.artist;
        document.getElementById("play-title").textContent = record.title;
        trackEl.textContent = track ? track.title : "";
        sideLabel.textContent = "Side " + side.id;
    }
}

function renderLink() {
    var record = getLinkRecord();
    var cover = document.getElementById("link-cover");
    var artist = document.getElementById("link-artist");
    var title = document.getElementById("link-title");
    var idEl = document.getElementById("link-id");
    var statusEl = document.getElementById("link-status");
    var errorEl = document.getElementById("link-error");

    if (record) {
        cover.src = coverImageUrl(record);
        idEl.textContent = String(record.id).padStart(2, "0");
        artist.textContent = record.artist;
        title.textContent = record.title;

        if (state.linkError) {
            statusEl.style.display = "none";
            errorEl.style.display = "";
        } else {
            statusEl.textContent = record.linked ? "Linked" : "Not Linked";
            statusEl.style.display = "";
            errorEl.style.display = "none";
        }
    }
}

function renderReLink() {
    var record = getReLinkRecord();
    var cover = document.getElementById("re-link-cover");
    var artist = document.getElementById("re-link-artist");
    var title = document.getElementById("re-link-title");
    var idEl = document.getElementById("re-link-id");
    var statusEl = document.getElementById("re-link-status");
    var errorEl = document.getElementById("re-link-error");

    if (record) {
        cover.src = coverImageUrl(record);
        idEl.textContent = String(record.id).padStart(2, "0");
        artist.textContent = record.artist;
        title.textContent = record.title;

        if (state.linkError) {
            statusEl.style.display = "none";
            errorEl.style.display = "";
        } else {
            statusEl.textContent = "Linked";
            statusEl.style.display = "";
            errorEl.style.display = "none";
        }
    }
}

function renderStylus() {
    var stylus = getCurrentStylus();
    var nameEl = document.getElementById("stylus-mode-name");
    var hoursEl = document.getElementById("stylus-mode-hours");
    var barFill = document.getElementById("stylus-bar-full-fill");
    var bar = document.getElementById("stylus-bar-full");
    var empty = document.getElementById("stylus-empty");

    if (stylus) {
        var hours = getStylusHours(stylus);
        var ratio = getBarFillRatio(hours, stylus.capacity_max);
        var color = getBarColor(hours, stylus.capacity_min);

        nameEl.textContent = stylus.name;
        nameEl.style.display = "";
        hoursEl.textContent = hours + " h";
        hoursEl.style.display = "";
        bar.style.display = "";
        barFill.style.width = (ratio * 100) + "%";
        barFill.style.background = "var(" + color + ")";
        empty.style.display = "none";
    } else {
        nameEl.style.display = "none";
        hoursEl.style.display = "none";
        bar.style.display = "none";
        empty.style.display = "";
    }
}

// ---------------------------------------------------------------------------
// REST API
// ---------------------------------------------------------------------------

function fetchRecords() {
    return fetch("/records")
        .then(function (res) { return res.json(); })
        .then(function (data) { state.records = data; })
        .catch(function (e) { console.error("Failed to fetch records:", e); });
}

function fetchStyli() {
    return fetch("/styli")
        .then(function (res) { return res.json(); })
        .then(function (data) { state.styli = data; })
        .catch(function (e) { console.error("Failed to fetch styli:", e); });
}

function fetchTemperature() {
    return fetch("/temperature")
        .then(function (res) { return res.json(); })
        .then(function (data) {
            state.temperature = data.celsius;
            render();
        })
        .catch(function () {
            state.temperature = null;
            render();
        });
}

function linkRecord() {
    var record = getLinkRecord();
    if (!record) return;

    fetch("/records/" + record.id + "/link", { method: "POST" })
        .then(function (res) {
            if (res.ok) {
                record.linked = true;
                state.linkError = false;
            } else {
                state.linkError = true;
            }
            render();
        })
        .catch(function () {
            state.linkError = true;
            render();
        });
}

function resetStylus() {
    var stylus = getCurrentStylus();
    if (!stylus) return;

    fetch("/styli/" + stylus.id + "/reset", { method: "POST" })
        .then(function (res) {
            if (res.ok) {
                stylus.hours = 0;
                state.stylusHours[stylus.id] = 0;
            }
            render();
        })
        .catch(function (e) {
            console.error("Failed to reset stylus:", e);
        });
}

// ---------------------------------------------------------------------------
// Navigation
// ---------------------------------------------------------------------------

function prevRecord() {
    if (state.records.length === 0) return;
    state.linkRecordIndex = (state.linkRecordIndex - 1 + state.records.length) % state.records.length;
    state.linkError = false;
    render();
}

function nextRecord() {
    if (state.records.length === 0) return;
    state.linkRecordIndex = (state.linkRecordIndex + 1) % state.records.length;
    state.linkError = false;
    render();
}

function prevReLinkRecord() {
    var linked = getLinkedRecords();
    if (linked.length === 0) return;
    state.reLinkRecordIndex = (state.reLinkRecordIndex - 1 + linked.length) % linked.length;
    state.linkError = false;
    render();
}

function nextReLinkRecord() {
    var linked = getLinkedRecords();
    if (linked.length === 0) return;
    state.reLinkRecordIndex = (state.reLinkRecordIndex + 1) % linked.length;
    state.linkError = false;
    render();
}

function prevStylus() {
    if (state.styli.length === 0) return;
    state.stylusIndex = (state.stylusIndex - 1 + state.styli.length) % state.styli.length;
    render();
}

function nextStylus() {
    if (state.styli.length === 0) return;
    state.stylusIndex = (state.stylusIndex + 1) % state.styli.length;
    render();
}

function prevSong() {
    var record = getCurrentRecord();
    if (!record || !record.sides || record.sides.length === 0) return;

    state.currentTrackIndex--;
    if (state.currentTrackIndex < 0) {
        state.currentSideIndex = (state.currentSideIndex - 1 + record.sides.length) % record.sides.length;
        state.currentTrackIndex = record.sides[state.currentSideIndex].tracks.length - 1;
    }
    render();
}

function nextSong() {
    var record = getCurrentRecord();
    if (!record || !record.sides || record.sides.length === 0) return;

    var side = record.sides[state.currentSideIndex];
    state.currentTrackIndex++;
    if (state.currentTrackIndex >= side.tracks.length) {
        state.currentSideIndex = (state.currentSideIndex + 1) % record.sides.length;
        state.currentTrackIndex = 0;
    }
    render();
}

function switchSide() {
    var record = getCurrentRecord();
    if (!record || !record.sides || record.sides.length === 0) return;

    state.currentSideIndex = (state.currentSideIndex + 1) % record.sides.length;
    state.currentTrackIndex = 0;
    render();
}

// ---------------------------------------------------------------------------
// WebSocket
// ---------------------------------------------------------------------------

function connectWebSocket() {
    var protocol = location.protocol === "https:" ? "wss:" : "ws:";
    var ws = new WebSocket(protocol + "//" + location.host + "/ws");

    ws.onmessage = function (event) {
        var msg = JSON.parse(event.data);

        switch (msg.event) {
            case "current_record":
                state.currentRecordId = msg.data.record_id;
                state.currentTrackIndex = 0;
                state.currentSideIndex = 0;
                render();
                break;
            case "stylus_hours":
                state.stylusHours[msg.data.stylus_id] = msg.data.hours;
                render();
                break;
            case "status":
                if (!location.hash) {
                    if (msg.data.status === "playing" && state.mode === "standby") {
                        state.mode = "play";
                        render();
                    } else if (msg.data.status === "idle" && state.mode === "play") {
                        state.mode = "standby";
                        render();
                    }
                }
                break;
            case "temperature_c":
                state.temperature = msg.data.temp_c;
                break;
        }
    };

    ws.onclose = function () {
        setTimeout(connectWebSocket, 3000);
    };

    ws.onerror = function () {
        ws.close();
    };
}

// ---------------------------------------------------------------------------
// Dev mode — URL hash navigation
// ---------------------------------------------------------------------------

function applyHash() {
    var hash = location.hash.replace(/^#/, "");
    if (!hash) return false;

    // Handle re-link as a mode
    var mode;
    var rest;
    if (hash === "re-link" || hash.indexOf("re-link-") === 0) {
        mode = "re-link";
        rest = hash.slice("re-link-".length);
    } else {
        var parts = hash.split("-");
        mode = parts[0];
        rest = parts.slice(1).join("-");
    }

    var isError = rest === "error";

    if (MODES.indexOf(mode) === -1) return false;

    state.mode = mode;
    state.linkError = false;
    state.standbyError = null;

    // Restore currentRecordId from fetched data
    if (state.records.length > 0) {
        state.currentRecordId = state.records[0].id;
    }

    if (isError) {
        switch (mode) {
            case "standby":
                state.standbyError = "nfc";
                break;
            case "link":
                state.linkError = true;
                break;
            case "stylus":
                state.styli = [];
                break;
        }
    }

    // For re-link mode, mark all records as linked for demo
    if (mode === "re-link") {
        state.records.forEach(function (r) { r.linked = true; });
    }

    // Handle standby-not-found hash
    if (mode === "standby" && rest === "not-found") {
        state.standbyError = "not-found";
    }

    render();
    return true;
}

// ---------------------------------------------------------------------------
// Init
// ---------------------------------------------------------------------------

document.addEventListener("DOMContentLoaded", function () {
    Promise.all([fetchRecords(), fetchStyli()]).then(function () {
        if (!applyHash()) {
            render();
        }
        connectWebSocket();
        fetchTemperature();
        setInterval(fetchTemperature, 30000);
    });

    window.addEventListener("hashchange", function () {
        // Re-fetch data to reset any error overrides before applying hash
        Promise.all([fetchRecords(), fetchStyli()]).then(function () {
            if (!applyHash()) {
                render();
            }
        });
    });

    // Button event listeners
    document.getElementById("btn-side-standby").addEventListener("click", switchSide);

    document.getElementById("btn-prev-song").addEventListener("click", prevSong);
    document.getElementById("btn-next-song").addEventListener("click", nextSong);
    document.getElementById("btn-side-label").addEventListener("click", switchSide);

    document.getElementById("btn-prev-record").addEventListener("click", prevRecord);
    document.getElementById("btn-next-record").addEventListener("click", nextRecord);

    document.getElementById("btn-prev-re-link").addEventListener("click", prevReLinkRecord);
    document.getElementById("btn-next-re-link").addEventListener("click", nextReLinkRecord);

    document.getElementById("btn-prev-stylus").addEventListener("click", prevStylus);
    document.getElementById("btn-next-stylus").addEventListener("click", nextStylus);
});
